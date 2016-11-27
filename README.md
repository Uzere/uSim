uSim
====
uSim is a fork of [SimPy](https://bitbucket.org/simpy/simpy) made to replace GPSS in BMSTU education process.

SimPy
-----

SimPy is a process-based discrete-event simulation framework based on standard
Python. Processes in SimPy are defined by Python [generator](http://docs.python.org/3/glossary.html#term-generator) functions and
can, for example, be used to model active components like customers, vehicles or
agents.  SimPy also provides various types of shared resources to model
limited capacity congestion points (like servers, checkout counters and
tunnels).

Simulations can be performed “as fast as possible”, in real time (wall clock
time) or by manually stepping through the events.

Though it is theoretically possible to do continuous simulations with SimPy, it
has no features that help you with that. Also, SimPy is not really required for
simulations with a fixed step size and where your processes don’t interact with
each other or with shared resources.

The [documentation](https://simpy.readthedocs.io/en/latest/) contains a [tutorial](https://simpy.readthedocs.io/en/latest/simpy_intro/index.html), [several guides](https://simpy.readthedocs.io/en/latest/topical_guides/index.html) explaining key
concepts, a number of [examples](https://simpy.readthedocs.io/en/latest/examples/index.html) and the [API reference](https://simpy.readthedocs.io/en/latest/api_reference/index.html).

SimPy is released under the MIT License. Simulation model developers are
encouraged to share their SimPy modeling techniques with the SimPy community.
Please post a message to the [SimPy mailing list](https://groups.google.com/forum/#!forum/python-simpy).

There is an introductory talk that explains SimPy’s concepts and provides some
examples: [watch the video](https://www.youtube.com/watch?v=Bk91DoAEcjY) or [get the slides](http://stefan.sofa-rockers.org/downloads/simpy-ep14.pdf).

A Simple Example
----------------

One of SimPy's main goals is to be easy to use. Here is an example for a simple
SimPy simulation: a *clock* process that prints the current simulation time at
each step:

```python

>>> import simpy
>>>
>>> def clock(env, name, tick):
...     while True:
...         print(name, env.now)
...         yield env.timeout(tick)
...
>>> env = simpy.Environment()
>>> env.process(clock(env, 'fast', 0.5))
<Process(clock) object at 0x...>
>>> env.process(clock(env, 'slow', 1))
<Process(clock) object at 0x...>
>>> env.run(until=2)
fast 0
slow 0
fast 0.5
slow 1
fast 1.0
fast 1.5
```

Installation
------------

SimPy requires Python 2.7, 3.2, PyPy 2.0 or above.

You can install SimPy easily via `pip <http://pypi.python.org/pypi/pip>`_:

```bash
$ pip install -U simpy
```

You can also download and install SimPy manually:

```bash
$ cd where/you/put/simpy/
$ python setup.py install
```

To run SimPy’s test suite on your installation, execute:

```bash
$ py.test --pyargs simpy
```

Getting started
---------------

If you’ve never used SimPy before, the [SimPy tutorial](https://simpy.readthedocs.io/en/latest/simpy_intro/index.html) is a good starting
point for you. You can also try out some of the [Examples](https://simpy.readthedocs.io/en/latest/examples/index.html) shipped with SimPy.


Documentation and Help
----------------------

You can find [a tutorial](https://simpy.readthedocs.io/en/latest/simpy_intro/index.html),
[examples](https://simpy.readthedocs.io/en/latest/examples/index.html), [topical guides](https://simpy.readthedocs.io/en/latest/topical_guides/index.html)
and an [API reference](https://simpy.readthedocs.io/en/latest/api_reference/index.html), as well as some information about
[SimPy and its history](https://simpy.readthedocs.io/en/latest/about/index.html) in our [online documentation](https://simpy.readthedocs.io/).
For more help, contact the [SimPy mailing list](mailto:python-simpy@googlegroups.com). SimPy users are pretty helpful. 
You can, of course, also dig through the [source code](https://bitbucket.org/simpy/simpy/src).

If you find any bugs, please post them on our [issue tracker](https://bitbucket.org/simpy/simpy/issues?status=new&status=open).

Enjoy simulation programming in SimPy!


Ports
-----

Reimplementations of SimPy are available in the following languages:

- C#: [SimSharp](https://github.com/abeham/SimSharp) (written by Andreas Beham)
- Julia: [SimJulia](https://github.com/BenLauwens/SimJulia.jl)
- R: [Simmer](https://github.com/r-simmer/simmer)
