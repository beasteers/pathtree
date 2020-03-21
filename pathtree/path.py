import os
import glob
import pathlib
from functools import wraps
import inspect
from parse import parse as parse_
from pformat import *

__all__ = ['Paths', 'Path', 'tree']

def tree(root='.', paths=None, data=None):
    '''Build paths from a directory spec.

    Arguments:
        root (str): the root directory.
        paths (dict): the directory structure.

    Returns:
        The initialized Paths object
    '''
    if isinstance(root, dict):
        root, paths = '.', root
    return Paths(
        {v: Path(*k) for k, v in get_keys({'{root}': {'': 'root', **paths}})},
        dict(data or {}, root=root))


def parse(pattern, s):
    r = parse_(pattern, s)
    return r and r.named


class UnderspecifiedError(KeyError):
    pass


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

    @wraps(tree)
    @classmethod
    def define(cls, *a, **kw):
        return tree(*a, **kw)


    @property
    def paths(self):
        return self._paths

    @property
    def copy(self):
        return Paths({name: path.copy for name, path in self.paths.items()},
                     dict(self.data))

    def add(self, root, paths):
        '''Build paths from a directory spec.

        Arguments:
            root (str): the root directory.
            paths (dict): the directory structure.

        Returns:
            The initialized Paths object
        '''
        root = (root if isinstance(root, Path) else self.paths[root]).path_pattern
        paths = paths if isinstance(paths, Paths) else tree(paths)

        # add paths to
        self.paths.update(**{
            k: p.repath(p.format_only(root=root))
            for k, p in paths.paths.items()})

        for path in paths.paths.values():
            path.parent = self
        return self

    def __repr__(self):
        return '<Paths data={} \n{}\n>'.format(self.data, '\n'.join([
            '\t{} : {}'.format(name, self[name].maybe_format())
            for name in self.paths
        ]))

    def __iter__(self):
        return iter(self.paths)

    def __getitem__(self, name):
        return self.paths[name]

    def __getattr__(self, name):
        try:
            return self.paths[name]
        except KeyError:
            raise AttributeError()

    def parse(self, path, name):
        '''Parse data from a formatted string (reverse of string format)

        Arguments:
            path (str): the string to parse
            name (str): the name of the path pattern to use.
        '''
        return self[name].parse(path)

    def translate(self, file, form, to, **kw):
        return self[to].specify(**self[form].parse(file, **kw))

    def makedirs(self):
        '''Instantiate all fully specified directories.'''
        for path in self.paths.values():
            try:
                path.make(up=1)
            except UnderspecifiedError:
                pass

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
            p.data.pop(key, None)
        return p

    @property
    def fully_specified(self):
        '''Are all paths fully specified?'''
        return all(p.fully_specified for p in self.paths.values())

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
    __FORBIDDEN_KEYS__ = ()
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
        return '<Path "{}" data={}>'.format(self.path_pattern, self.path_data)

    def __getattr__(self, name):
        return getattr(self.path, name)

    @property
    def path_pattern(self):
        '''The path as an unformatted string'''
        return str(self._path)

    @property
    def path(self):
        '''Get the formatted path as a pathlib.Path object'''
        return pathlib.Path(self.format())

    @property
    def s(self):
        '''Convert to string'''
        return str(self)

    @property
    def path_data(self):
        '''Both the path specific data and the paths group data'''
        return {**self.parent.data, **self.data} if self.parent else self.data

    def update(self, **kw):
        '''Update specified data in place'''
        self.data.update(**{k: v for k, v in kw.items() if k not in self.__FORBIDDEN_KEYS__})
        return self

    def specify(self, **kw):
        '''Update specified data and return a new object'''
        return self.copy.update(**kw)

    def unspecify(self, *keys, parent=True):
        '''Remove keys from path dictionary'''
        p = self.copy
        if parent and p.parent:
            p.parent = p.parent.unspecify(*keys)

        for key in keys:
            p.data.pop(key, None)
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
    def safe(self):
        '''Make sure the path does not go above root.'''
        return self.repath(os.path.normpath(os.sep + str(self._path)).lstrip(os.sep))

    def repath(self, *f, data=None):
        '''Make a copy with an entirely new path.'''
        return Path(*f, data=dict(self.data, **(data or {})), parent=self.parent)

    def join(self, *f):
        '''Make a copy and append directories to the end.'''
        return self.repath(self._path, *f)

    j = join

    @property
    def copy(self):
        '''Create a copy of the path object.'''
        return self.join()

    def up(self, n=1):
        '''Create a copy of the path object up one directory.'''
        return self.repath(
            os.path.normpath(os.path.join(self._path, *(['..']*n))))

    def find_sibling(self, name):
        '''Find another path in the root tree.'''
        try:
            return self.parent[name]
        except (AttributeError, TypeError) as e:
            raise AttributeError('No related paths are available.')
        except KeyError as e:
            raise KeyError('No related paths by that name are available.')

    def format(self, **kw):
        '''Insert data into the path string. (Works like string format.)

        Raises:
            KeyError if the format string is underspecified.
        '''
        try:
            return self.path_pattern.format(**{**self.path_data, **kw})
        except KeyError as e:
            raise UnderspecifiedError(str(e))

    def parse(self, path, use_data=True):
        '''Extract variables from a compiled path'''
        pattern = self.partial_format() if use_data else self.path_pattern
        data = parse(pattern, path)
        if not data:
            raise ValueError(inspect.cleandoc('''
                Could not parse path using pattern.
                    path:{}
                    pattern:{}

                `path.parse(path)` will call self.partial_format() by default before parsing
                so any specified keys will be fixed. This is helpful to dodge ambiguous parsing
                cases. To disable this pass `use_data=False` to parse.
                '''.format(path, pattern)))
        return {**self.path_data, **data}

    def translate(self, path, to, **kw):
        '''Translate the paths to another pattern'''
        return self.find_sibling(to).specify(**self.parse(path, **kw))

    def maybe_format(self, **kw):
        '''Try to format a field. If it fails, return as a Path object.'''
        p = self.specify(**kw)
        try:
            return p.format()
        except KeyError:
            return p

    def partial_format(self, **kw):
        '''Format a field, leaving all unspecified fields to be filled later.'''
        f = pformat(self.path_pattern, **{**self.path_data, **kw})
        return f

    def format_only(self, **kw):
        return pformat(self.path_pattern, **kw)

    @property
    def glob_pattern(self):
        '''Format a field, setting all unspecified fields as a wildcard (asterisk).'''
        return gformat(self.path_pattern, **self.path_data)

    def glob(self, *f):
        '''Find all matching files. unspecified fields are set as a wildcard (asterisk).'''
        return sglob(self.glob_pattern, *f)

    def iglob(self, *f):
        '''Find all matching files as a generator.'''
        return glob.iglob(os.path.join(self.glob_pattern, *f))

    def rglob(self, *f):
        '''Find all matching files recursively as a generator.'''
        return self.path.rglob(os.path.join(*(f or '*')))

    def make(self, up=0):
        '''Create this (or up a) directory.'''
        os.makedirs(self.up(up), exist_ok=True)
        return self

    def touch(self, *a, **kw):
        '''Touch this file - will recursively create parent directories.'''
        self.make(up=1).path.touch(*a, **kw)
        return self

    def rm(self):
        '''Remove this file or directory.'''
        p = self.safe
        p.rmdir() if self.is_dir() else os.remove(p.format()) if self.is_file() else None
        return self

    def rmglob(self, *f, include=False):
        '''Recursively remove files matching join(*f). Set include=True, to
        remove this node as well.'''
        fs = sorted(self.safe.rglob(*f), key=lambda p: p.parts, reverse=True)
        for fi in fs:
            fi.rmdir() if fi.is_dir() else os.remove(fi)
        if include:
            self.rm()
        return self

    def write(self, x, mode='', **kw):
        '''Write to file. Set mode='b' to write as bytes.'''
        self.make(1)
        b = 'b' in mode if mode else isinstance(x, (bytes, bytearray))
        self.write_bytes(x, **kw) if b else self.write_text(x, **kw)
        return self

    def read(self, mode='', **kw):
        '''Read file. Set mode='b' to read as bytes.'''
        return self.read_bytes(**kw) if 'b' in mode else self.read_text(**kw)



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

example = tree({
    'data': {
        '{date}': {
            '': 'date',
            '{labels_set}.csv': 'csv',
            'flac': {
                '': 'flac_root',
                '{name}.flac': 'flac',
            }
        }
    }
})
