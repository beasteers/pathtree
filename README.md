# pathtree
Named path hierarchies

The goal of this package is to make it easier to both define and understand folder structures in your scripts and pipelines. I find it difficult to visualize file structure when looking at a series of `os.path.join` commands scattered throughout a script, so instead, you define all of the paths up top, and fill in the placeholders later.

## Install

```bash
pip install path-tree
```

## Tutorial

### Quick start

```python
import pathtree

paths = pathtree.paths('./logs', {
    '{log_id}': {
        'model.h5': 'model',
        'model_spec.pkl': 'model_spec',
        'plots': {
            'epoch_{i_epoch:04d}': {
                '{plot_name}.png': 'plot',
                '': 'plot_dir'
            }
        }
    }
})

...

paths.update(log_id=12345)

...

plt.imwrite(paths.plot.format(i_epoch=5, plot_name='f1_score'))
# writes to ./logs/12345/plots/epoch_0005/f1_score.png
```

### The old way - makes my brain sad

Usually, you end up defining paths doing something like this (unless I'm doing something weird/dumb - lmk !!). And often,
these end up scattered throughout your project and getting a high level
picture of your path hierarchy is difficult.

```python
base_log_dir = './blah/logs'
run_dir = os.path.join(base_log_dir, log_id)
resources_dir = os.path.join(run_dir, 'resources')

...

model_file = os.path.join(run_dir, 'model.h5')
model_spec = os.path.join(run_dir, 'model_spec.pkl')

...

pump_file = os.path.join(resources_dir, 'pump.pkl')

...

plot_dir = os.path.join(run_dir, 'plots', 'epoch_{i_epoch:04d}')
plot_file = os.path.join(plot_dir, '{plot_name}.png')
```

### The new way ! **\*brain smiles\***

Instead, you can define your path hierarchy all in one place and give each tree node a name.

```python
import os
import pathtree

# define the entire directory structure
# the tree keys represent folder names.
# the final non-dict key represents the name for
# that directory node.
#
# e.g.: {folder1: {folder2: name}}
# paths.name => folder1/folder2
#
# Notice the blank key under "plots". This takes advantage
# of the fact that os.path.join('plots', '') == 'plots'.
# So the name assigned to the blank string is naming the
# directory
base_paths = pathtree.paths('./logs', {
    '{log_id}': {
        'model.h5': 'model',
        'model_spec.pkl': 'model_spec',
        'plots': {
            'epoch_{i_epoch:04d}': {
                '{plot_name}.png': 'plot',
                '': 'plot_dir'
            }
        }
    }
})

# specify the log_id
paths = base_paths.specify(log_id=12345)

```

#### Conversion to string

You can access the paths using the name defined in the tree:

```python
assert str(paths.model_spec) == './logs/12345/model_spec.pkl'
```

A `Paths` object (as defined above) is really just a dictionary of name => `pathtree.Path` objects. This is a wrapper around string format pattern and a data dictionary.

To convert a `Path` to a string, there are a few ways to get what you want.

For fully specified strings (meaning that str.format will run without a KeyError), all three of these methods return the same thing: a fully formatted string.

```python
assert paths.model.format() == './logs/12345/model.h5'
assert paths.model.partial_format() == './logs/12345/model.h5'
assert paths.model.maybe_format() == './logs/12345/model.h5'
```

For an underspecified string (missing data keys), the return values are different:

```python
# str.format is missing a key and will throw an exception
try:
    paths.plot.format(plot_name='f1_score')
    assert False
except KeyError: # missing i_epoch
    assert True

# str.format is missing a key so the missing key will be left in
assert (paths.plot.partial_format(plot_name='f1_score') ==  
        './logs/12345/plots/epoch_{i_epoch:04d}/f1_score.png')

# str.format is missing a key so it will keep it as a Path object
# with the updated key `plot_name`.
# this retains the ability to use data updating functionality.
assert isinstance(
    paths.plot.maybe_format(plot_name='f1_score'), pathtree.Path)
```

Paths are castable to string which is the same as `partial_format`. You can also access the unformatted path using `Path().path`.

```python
assert str(paths.plot) == paths.plot.partial_format()
assert paths.plot.path == the_unformatted_plot_path
```

`pathtree.Path` subclasses `os.PathLike`, meaning that os.path functions know how to convert it to a path automatically.

```python
assert isinstance(paths.model, os.PathLike)
assert os.path.join(paths.model) == paths.model.format()
assert os.path.isfile(paths.model)
```

#### Updating format data

You can add path specificity at various points along the way. This is helpful when you need to reference subdirectories based on some loops or similar pattern. You can do that in a couple ways:

```python

# across the entire directory object

# update in place
paths.update(log_id=12345)

# or create a copy
paths2 = paths.specify(log_id=23456)
assert paths.data['log_id'] == 12345 and paths2.data['log_id'] = 23456

# reverse specify - remove a data key
paths2 = paths2.unspecify('log_id')
assert 'log_id' not in paths2.data

# or for a single path

# in place
plot_file = paths.plot
plot_file.update(plot_name='f1_score')

# create a copy
plot_file = paths.plot.specify(plot_name='f1_score')

assert 'plot_name' not in paths.data
assert plot_file.data['plot_name'] == 'f1_score'

# reverse specify - remove a data key
plot_file = plot_file.unspecify('plot_name')
assert 'plot_name' not in plot_file.data
```

### Additional Features

You can automatically do glob searching. Any missing fields will be filled with a glob wildcard (asterisk). Note that this would fail using plain string format because the leading zero formatter (`:04d`) will throw an error if you try to insert `'*'` (because it's a string).

```python
plot_file = paths.plot.specify(plot_name='f1_score')

assert (plot_file.partial_format() ==
        './logs/12345/plots/epoch_{i_epoch:04d}/f1_score.png')
assert (plot_file.glob_pattern ==
        './logs/12345/plots/epoch_*/f1_score.png')
assert (plot_file.glob() ==
        glob.glob('./logs/12345/plots/epoch_*/f1_score.png'))
```

You can also sometimes parse out data from a formatted string. Be warned,
it may not always work correctly because sometimes the parsing is ambiguous. See https://github.com/r1chardj0n3s/parse#potential-gotchas

```python
plot_file = paths.plot.specify(root='some/logs')

assert (plot_file.partial_format() ==
        'some/logs/12345/plots/epoch_{i_epoch:04d}/{plot_name}.png')

expected = {
    'root': 'some/logs'
    'log_id': '12345',
    'i_epoch': '0002',
    'plot_name': 'f1_score.png',
}


plot_data = plot_file.parse('./logs/12345/plots/0002/f1_score.png')
assert set(plot_data.items()) == set(expected.items())
```

### Usage Example
Here's a screenshot from one of the projects I'm using pathtree in and I really like how it simplifies defining the structure of your project files. I'm able to take a bunch of h5 files, parse out the path components, and translate them to their corresponding audio and jams file in another directory all while keeping a single point of truth for my file structure in the path definition. :)
![jupyter lab usage example](/assets/example.png)
