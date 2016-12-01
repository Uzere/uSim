"""
A collection of utility functions:

.. autosummary::
   start_delayed

"""
from collections import defaultdict


def start_delayed(env, generator, delay):
    """Return a helper process that starts another process for *generator*
    after a certain *delay*.

    :meth:`~simpy.core.Environment.process()` starts a process at the current
    simulation time. This helper allows you to start a process after a delay of
    *delay* simulation time units::

        >>> from simpy import Environment
        >>> from simpy.util import start_delayed
        >>> def my_process(env, x):
        ...     print('%s, %s' % (env.now, x))
        ...     yield env.timeout(1)
        ...
        >>> env = Environment()
        >>> proc = start_delayed(env, my_process(env, 3), 5)
        >>> env.run()
        5, 3

    Raise a :exc:`ValueError` if ``delay <= 0``.

    """
    if delay <= 0:
        raise ValueError('delay(=%s) must be > 0.' % delay)

    def starter():
        yield env.timeout(delay)
        proc = env.process(generator)
        env.exit(proc)

    return env.process(starter())


def subscribe_at(event):
    """Register at the *event* to receive an interrupt when it occurs.

    The most common use case for this is to pass
    a :class:`~simpy.events.Process` to get notified when it terminates.

    Raise a :exc:`RuntimeError` if ``event`` has already occurred.

    """
    env = event.env
    subscriber = env.active_process

    def signaller(signaller, receiver):
        result = yield signaller
        if receiver.is_alive:
            receiver.interrupt((signaller, result))

    if event.callbacks is not None:
        env.process(signaller(event, subscriber))
    else:
        raise RuntimeError('%s has already terminated.' % event)


class ProcessReport(object):
    @staticmethod
    def getReport(process):
        env = process.env
        reportKey = ProcessReport.getReportKey(process)

        if reportKey not in env.processReport:
            env.processReport[reportKey] = ProcessReport(process)

        return env.processReport[reportKey]


    @staticmethod
    def getReportKey(process):
        if process.report=='sum':
            return process._generator.__name__
        elif process.report=='row?':
            return process._generator.__name__ + '__' + str(process._generator.__hash__())
        else:
            raise ValueError('Report type should be "sum", "row?" or False')


    def __init__(self, process):
        self.name = ProcessReport.getReportKey(process)
        self.file = process._generator.gi_code.co_filename
        self.line = process._generator.gi_code.co_firstlineno

        self.count = defaultdict(int) # key - line no of generator's yield, val - count
        self.throwCount = defaultdict(int)


    def __repr__(self):
        return (
            self.file+' '+self.name+':'+str(self.line) + '\n' +
            self.count.__repr__() + '\n' +
            self.throwCount.__repr__() + '\n'
        )