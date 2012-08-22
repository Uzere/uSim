from heapq import heappush, heappop
from itertools import count
from types import GeneratorType

from simpy.exceptions import Interrupt, Failure, SimEnd


# Event types
Failed = 0
Success = 1
Init = 2
Suspended = 3

Infinity = float('inf')

Event = object()
"""Yielded by a PEM if it waits for an event (e.g. via "yield ctx.hold(1))."""


class Process(object):
    """A *Process* is a wrapper for instantiated PEMs.

    A Processes needs a unique process ID (*pid*) and a process event
    generator (*peg* -- the generator that the PEM returns).

    The *Process* class contains internal and external status
    information. It is also used for process interaction, e.g., for
    interruptions.

    """
    __slots__ = ('pid', 'peg', 'state', 'result',
            '_next_event', '_joiners', '_signallers', '_interrupts')

    def __init__(self, pid, peg):
        self.pid = pid
        self.peg = peg

        self.state = None
        self.result = None

        self._next_event = None
        self._joiners = []
        self._signallers = []
        self._interrupts = []

    def __repr__(self):
        """Return a string "Process(pid, pem_name)"."""
        return '%s(%s, %s)' % (self.__class__.__name__, self.pid,
                               self.peg.__name__)


def start(sim, pem, *args, **kwargs):
    peg = pem(sim.context, *args, **kwargs)
    assert type(peg) is GeneratorType, (
            'Process function %s is did not return a generator' % pem)
    proc = Process(next(sim.pid), peg)

    prev, sim.active_proc = sim.active_proc, proc
    # Schedule start of the process.
    sim._schedule(proc, Init, None)
    sim.active_proc = prev

    return proc


def exit(sim, result=None):
    sim.active_proc.result = result
    raise StopIteration()


def hold(sim, delta_t):
    assert delta_t >= 0
    proc = sim.active_proc
    assert proc._next_event is None

    sim._schedule(proc, Success, None, sim._now + delta_t)
    return Event


def resume(sim, other, value=None):
    if other._next_event is not None:
        assert other._next_event[0] != Init, (
                '%s is not initialized' % other)
    # TODO Isn't this dangerous? If other has already been resumed, this
    # call will silently drop the previous result.
    sim._schedule(other, Success, value)
    return Event


def interrupt(sim, other, cause=None):
    assert other._next_event[0] != Init, (
            '%s is not initialized' % other)

    interrupts = other._interrupts
    if not interrupts:
        # This is the first interrupt, so schedule it.
        sim._schedule(other,
                Success if other._next_event[0] == Suspended else Failed,
                None)

    interrupts.append(cause)


def signal(sim, other):
    """Interrupt this process, if the target terminates."""
    proc = sim.active_proc

    if other.peg is None:
        # FIXME This context switching is ugly.
        prev, sim.active_proc = sim.active_proc, other
        sim._schedule(proc, Failed, Interrupt(other))
        sim.active_proc = prev
    else:
        other._signallers.append(proc)


class Context(object):
    def __init__(self, sim):
        self._sim = sim

    @property
    def active_process(self):
        """Return the currently active process."""
        return self._sim.active_proc

    @property
    def now(self):
        """Return the current simulation time."""
        return self._sim._now


class Simulation(object):
    context_funcs = (start, exit, interrupt, hold, resume, signal)
    simulation_funcs = (start, interrupt, resume)

    def __init__(self):
        self.events = []

        self.pid = count()
        self.eid = count()
        self.active_proc = None
        self._now = 0

        # Instanciate the context and bind it to the simulation.
        self.context = Context(self)

        # Attach context function and bind them to the simulation.
        for func in self.context_funcs:
            setattr(self.context, func.__name__,
                    func.__get__(self, Simulation))

        # Attach public simulation functions to this instance.
        for func in self.simulation_funcs:
            setattr(self, func.__name__, func.__get__(self, Simulation))

    @property
    def now(self):
        return self._now

    def _schedule(self, proc, evt_type, value, at=None):
        if at is None:
            at = self._now

        proc._next_event = (evt_type, value)
        heappush(self.events, (at, next(self.eid), proc, proc._next_event))

    def _join(self, proc):
        joiners = proc._joiners
        signallers = proc._signallers
        interrupts = proc._interrupts

        proc.peg = None

        if proc.state == Failed:
            # TODO Don't know about this one. This check causes the whole
            # simulation to crash if there is a crashed process and no other
            # process to handle this crash. Something like this must certainely
            # be done, because exception should never ever be silently ignored.
            # Still, a check like this looks fishy to me.
            if not joiners and not signallers:
                raise proc.result.__cause__

        if joiners:
            for joiner in joiners:
                if joiner.peg is None: continue
                self._schedule(joiner, proc.state, proc.result)

        if signallers:
            for signaller in signallers:
                if signaller.peg is None: continue
                self._schedule(signaller, Failed, Interrupt(proc))

    def peek(self):
        """Return the time of the next event or ``inf`` if the event
        queue is empty.

        """
        try:
            while True:
                # Pop all removed events from the queue
                # self.events[0][3] is the scheduled event
                # self.events[0][2] is the corresponding proc
                if self.events[0][3] is self.events[0][2]._next_event:
                    break
                heappop(self.events)

            return self.events[0][0]  # time of first event

        except IndexError:
            return Infinity

    def step(self):
        assert self.active_proc is None

        while True:
            try:
                self._now, eid, proc, evt = heappop(self.events)
            except IndexError:
                raise SimEnd()

            # Break from the loop if we find a valid event.
            if evt is proc._next_event:
                break

        evt_type, value = evt
        proc._next_event = None
        self.active_proc = proc

        # Check if there are interrupts for this process.
        interrupts = proc._interrupts
        if interrupts:
            cause = interrupts.pop(0)
            value = cause if evt_type else Interrupt(cause)

        try:
            if evt_type:
                # A "successful" event.
                target = proc.peg.send(value)
            else:
                # An "unsuccessful" event.
                target = proc.peg.throw(value)
        except StopIteration:
            # Process has terminated.
            proc.state = Success
            self._join(proc)
            self.active_proc = None
            return
        except BaseException as e:
            # Process has failed.
            proc.state = Failed
            proc.result = Failure()
            proc.result.__cause__ = e
            self._join(proc)
            self.active_proc = None
            return

        if target is not None:
            if target is not Event:
                # TODO Improve this error message.
                assert type(target) is Process, 'Invalid yield value "%s"' % target
                # TODO The stacktrace won't show the position in the pem where this
                # exception occured. Maybe throw the assertion error into the pem?
                assert proc._next_event is None, 'Next event already scheduled!'

                # Add this process to the list of waiters.
                if target.peg is None:
                    # FIXME This context switching is ugly.
                    prev, self.active_proc = self.active_proc, target
                    # Process has already terminated. Resume as soon as possible.
                    self._schedule(proc, target.state, target.result)
                    self.active_proc = prev
                else:
                    # FIXME This is a bit ugly. Because next_event cannot be
                    # None this stub event is used. It will never be executed
                    # because it isn't scheduled. This is necessary for
                    # interrupt handling.
                    proc._next_event = (Success, None)
                    target._joiners.append(proc)
            else:
                assert proc._next_event is not None
        else:
            assert proc._next_event is None, 'Next event already scheduled!'
            proc._next_event = (Suspended, None)

        # Schedule concurrent interrupts.
        if interrupts:
            self._schedule(proc,
                    Success if proc._next_event[0] == Suspended else Failed,
                    None)

        self.active_proc = None

    def step_dt(self, delta_t=1):
        """Execute all events that occur within the next *delta_t*
        units of simulation time.

        """
        if delta_t <= 0:
            raise ValueError('delta_t(=%s) should be a number > 0.' % delta_t)

        until = self._now + delta_t
        while self.peek() < until:
            self.step()

    def simulate(self, until=Infinity):
        """Shortcut for ``while sim.peek() < until: sim.step()``."""
        if until <= 0:
            raise ValueError('until(=%s) should be a number > 0.' % until)

        while self.peek() < until:
            self.step()
