Exprec
======

Exprec records your experiments so you can compare different runs and easily reproduce results. Exprec is short for 'experiment recorder'. 


Installation
------------

```bash
pip install git+https://github.com/martno/exprec.git
```


Usage
-----

### Minimal example

```python
from exprec import Experiment

with Experiment() as experiment:
    pass
    # YOUR CODE HERE
```

All output within this `with` statement will be logged, which can later be accessed in the dashboard (see below). All python code and installed packages are recorded as well. 

### Dashboard

In your terminal:

```bash
exprec
```

Now visit http://localhost:9090/ in your browser to see the dashboard. If the client and exprec server are running on different machines, set the flag `--host=0.0.0.0`. 

### More code examples

```python
from exprec import Experiment

with Experiment(title='My experiment', tags=['tag1', 'tag2']) as experiment:
    experiment.set_parameter('test_parameter', 5)

    for i in range(10):
        experiment.add_scalar('2x', 2*i, step=i)
        experiment.add_scalar('3x', 3*i, step=i)

    with experiment.open('filename.txt', mode='w') as fp:
        fp.write('test\n')
        # This creates a file in the experiment's folder (`.experiments/<experiment-id>/files/filename.txt`). It can be
        # accessed by other experiments by calling
        # `with experiment.open('filename.txt', mode='r', uuid=previous_experiment_uuid) as fp:`.
        # When opening a previous experiment's file, the previous experiment will be referred to as 
        # the current experiment's 'parent' (shown in the summary in the dashboard). 

    raise ValueError('Invalid value')
    # The experiment will finish with status 'failed'. The exception is also logged. 
```


Examples
--------

Scripts under `examples/` demonstrates how to use this package. 


API
---

### Experiment

```python
Experiment(self, title='', tags=list, verbose=True, exceptions_to_ignore=[<class 'KeyboardInterrupt'>], name='') -> None
```

#### set_parameter

```python
Experiment.set_parameter(self, name, value)
```
Sets the parameter to the given value.

Only one value per parameter. You can overwrite a previously set parameter.

#### add_scalar

```python
Experiment.add_scalar(self, name, value, step=None)
```
Records the scalar's value at a given step.

The timestamp for setting this value is recorded as well, which can be accessed from the dashboard.

#### add_image

```python
Experiment.add_image(self, name, image, step)
```
Adds an image at a given step.

Args:
    name (str): The name of the image
    image: The image to save. Should either be a Pillow image, or a numpy array which can be converted to a Pillow image.
    step (int)

#### open

```python
Experiment.open(self, filename, mode='r', uuid=None)
```

Args:
    filename (str): A filename or path to a filename
    mode (str): The mode in which the file is opened. Supports the same modes as Python's built-in `open()` function.
    uuid (str, None): A previous experiment's id. If given, it will look for the filename in the previous experiment's
        saved files. Only supports 'r' mode when a uuid is given.
Returns:
    A file object


Licence
-------

MIT Licence

