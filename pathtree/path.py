import os
import glob
import pathlib
from functools import wraps
from .pformat import *

__all__ = ['Paths', 'Path', 'paths']

def paths(root, paths=None):
    '''Build paths from a directory spec.

    Arguments:
        root (str): the root directory.
        paths (dict): the directory structure.

    Returns:
        The initialized Paths object
    '''
    if isinstance(root, dict):
        root, paths = '.', root
    data = {'root': root} if root else {}

    return Paths({v: Path(*k) for k, v in get_keys({'{root}': paths})},
                 data)

class Paths(object):
    '''

    Example
    -------

    paths = Paths.define('./blah/logs', {
        '{log_id}': {
            'model.h5': 'model',
            'model_spec.pkl': 'model_spec',
            'plots': {
                '{step_name}': {
                    '{plot_name}.png': 'plot',
                    '': 'plot_dir'
                }
            }
        }
    })

    paths = paths.format(root='logs', log_id='adfasdfasdf', step_name='epoch_100')

    paths.model # logs/adfasdfasdf/model.h5
    paths.plot # logs/adfasdfasdf/plots/epoch_100/{plot_name}.png

    plot_files = glob.glob(paths['plot'].format(plot_name='*'))

    '''

    def __init__(self, paths, data=None):
        self._paths = paths
        self.data = {} if data is None else data

        for path in self._paths.values():
            path.parent = self

    @wraps(paths)
    @classmethod
    def define(cls, *a, **kw):
        return paths(*a, **kw)


    @property
    def paths(self):
        return self._paths

    @property
    def copy(self):
        return Paths({name: path.copy for name, path in self._paths.items()},
                     dict(self.data))

    def add(self, root, paths):
        '''Build paths from a directory spec.

        Arguments:
            root (str): the root directory.
            paths (dict): the directory structure.

        Returns:
            The initialized Paths object
        '''
        if not isinstance(paths, Paths):
            paths = Paths.define(None, {root: paths})

        self.paths.update(paths.paths)
        for path in paths.paths.values():
            path.parent = self
        return self

    def __repr__(self):
        return '<Paths data={} \n{}\n>'.format(self.data, '\n'.join([
            '\t{} : {}'.format(name, self[name].maybe_format())
            for name in self._paths
        ]))

    def __iter__(self):
        return iter(self._paths)

    def __getitem__(self, name):
        return self._paths[name].copy

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError()

    def get(self, name, **kw):
        '''Get a copy of a path object, optionally adding '''
        return self[name].update(**kw)

    def parse(self, path, name):
        '''Parse data from a formatted string (reverse of string format)

        Arguments:
            path (str): the string to parse
            name (str): the name of the path pattern to use.
        '''
        return self[name].parse(path)

    def mkdirs(self, exist_ok=True):
        '''Instantiate all fully specified directories'''
        for name, path in self.format().items():
            if path and not isinstance(path, Path):
                os.makedirs(os.path.dirname(path), exist_ok=exist_ok)

    def update(self, **kw):
        '''Update format data in place.'''
        self.data.update(kw)
        return self

    def specify(self, **kw):
        '''Return a new Paths object with added variables for each pattern.'''
        return self.copy.update(**kw)

    def unspecify(self, *keys):
        '''Remove keys from paths dictionary'''
        p = self.copy
        for key in keys:
            del p.data[key]
        return p

    @property
    def fully_specified(self):
        return all(p.fully_specified for p in self._paths)

    def format(self, **kw):
        '''Return a dictionary where all fully specified paths are converted to strings
        and underspecified strings are left as Path objects.

        Arguments:
            **kw: additional data specified for formatting.
        '''
        return {name: self[name].maybe_format(**kw) for name in self}

    def partial_format(self, **kw):
        '''Return a dictionary where all paths are converted to strings
        and underspecified fields are left in for later formatting.

        Arguments:
            **kw: additional data specified for formatting.
        '''
        return {name: self[name].partial_format(**kw) for name in self}

    def globs(self, *names):
        return [f for name in names for f in self[name].glob()]


class Path(os.PathLike):
    '''
    # define a path with missing parts
    path = Paths('blah/{something}/{huh}/what')
    # update data in place
    path.update(huh='um')
    # not all fields are defined
    assert not path.fully_specified
    # partial format will fill available fields
    assert str(path) == path.partial_format() == 'blah/{something}/um/what'

    # format will throw an error because there are missing keys
    try:
        path.format()
        assert False
    except KeyError:
        assert True

    # glob_pattern will fill missing keys with an asterisk
    assert path.glob_pattern == 'blah/*/um/what'

    # missing will convert to glob pattern and return all matching files
    assert isinstance(path.matching)
    '''
    def __init__(self, *path, data=None, parent=None):
        self._path = pathlib.Path(*path)
        self.data = {} if data is None else data
        self.parent = parent

    def __str__(self):
        '''The path as a string (partially formatted)'''
        return self.partial_format()

    def __fspath__(self):
        return self.format()

    def __repr__(self):
        return '<Path "{}" data={}>'.format(self.path, self.path_data)

    def __getattr__(self, name):
        return getattr(self._path, name)

    @property
    def path(self):
        '''The path object as a string (unformatted)'''
        return str(self._path)

    @property
    def path_data(self):
        '''Both the path specific data and the paths group data'''
        return {**self.parent.data, **self.data}

    def update(self, **kw):
        '''Update specified data in place'''
        self.data.update(**kw)
        return self

    def specify(self, **kw):
        '''Update specified data and return a new object'''
        return self.copy.update(**kw)

    def unspecify(self, *keys):
        '''Remove keys from path dictionary'''
        p = self.copy
        if p.parent:
            p.parent = p.parent.unspecify(*keys)

        for key in keys:
            del p.data[key]
        return p

    @property
    def fully_specified(self):
        '''Check if the path is fully specified.'''
        try:
            self.format()
            return True
        except KeyError:
            return False

    @property
    def unspecified(self):
        '''Get a path without any attached data.'''
        return Path(self._path)

    @property
    def copy(self):
        return Path(self._path, data=dict(self.data), parent=self.parent)

    def format(self, **kw):
        '''Insert data into the path string. (Works like string format.)

        Raises:
            KeyError if the format string is underspecified.
        '''
        return self.path.format(**{**self.path_data, **kw})

    def parse(self, path, use_data=True):
        '''Extract variables from a compiled path'''
        from parse import parse
        pattern = self.partial_format() if use_data else self.path
        r = parse(pattern, path)
        if not r:
            raise ValueError('Could not parse path using pattern '
                             '(\n\tpath:{}) (\n\tpattern:{})'.format(
                                 path, pattern))
        data = r.named
        return {**self.path_data, **data} if use_data else data

    def maybe_format(self, **kw):
        '''Try to format a field. If it fails, return as a Path object.'''
        p = self.specify(**kw)
        try:
            return p.format()
        except KeyError:
            return p

    def partial_format(self, **kw):
        '''Format a field, leaving all unspecified fields to be filled later.'''
        return pformat(self.path, **{**self.path_data, **kw})

    @property
    def glob_pattern(self):
        '''Format a field, setting all unspecified fields as a wildcard (asterisk).'''
        return gformat(self.path, **self.path_data)

    def glob(self):
        '''Find all matching files. unspecified fields are set as a wildcard (asterisk).'''
        return sorted(glob.glob(self.glob_pattern))

    def iglob(self):
        return glob.iglob(self.glob_pattern)



def sglob(*f):
    '''Enhanced glob. Pass path parts and return sorted list of files.'''
    return sorted(glob.glob(os.path.join(*f)))

def fbase(f, up=0):
    '''Return the file basename up x directories.'''
    return os.path.basename(os.path.abspath(os.path.join(f, *(['..']*up))))


def get_keys(data, keys=None):
    '''Recursively traverse a nested dict and return the trail of keys, and the final value'''
    keys = tuple(keys or ())
    for key, value in data.items():
        keys_ = keys + (key,)
        if isinstance(value, dict):
            for keys_, val in get_keys(value, keys_):
                yield keys_, val
        else:
            yield keys_, value
