Exprec
======

Exprec records your execution runs so you can compare different experiments and more easily reproduce results.


Installation
------------

```bash
pip install git+https://github.com/martno/exprec.git
```


Usage
-----

### Code example

```python
from exprec import Experiment

with Experiment() as experiment:
    pass
    # YOUR CODE HERE
```

All output in this with statement will be logged to a file which can later be accessed in the dashboard (see below). Also, all python code and installed packages are recorded as well. 

### Dashboard

In your terminal:

```bash
exprec
```

Now visit http://localhost:9090/ in your browser to see the dashboard. If the client and exprec server is running on different machines, set the flag `--host=0.0.0.0`. 

### More code examples

```python
from exprec import Experiment

with Experiment(name='experiment-1', tags=['tag1', 'tag2']) as experiment:
    experiment.set_parameter('test_parameter', 5)

    experiment.add_scalar('scalar1', 4, step=0)
    experiment.add_scalar('scalar1', 5, step=1)

    with experiment.open('filename.txt', mode='w') as fp:
        fp.write('test\n')
        # This creates a file in the experiment's folder (`.experiments/<experiment-id>/files/filename.txt`). It can be
        # accessed by other experiments using
        # `with experiment.open('filename.txt', mode='r', uuid=previous_experiment_uuid) as fp:`.
        # When opening a previous experiment's file, the previous experiment will be referred to as 
        # the current experiment's parent (shown in the summary in the dashboard). 

    raise ValueError('Invalid value')
    # The experiment will finish with status 'failed'. The exception is also logged. 
```


Licence
-------

MIT Licence

