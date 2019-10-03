import os
import glob
# import pathlib
from .pformat import *

__all__ = ['Paths']

class Paths(object):
    '''

    TODO:
     - how do you manage in both representations (flattened and hierarchical)
        - first step - manage in compiled view - assume unmutable
     - partial string substitution
     -

    -------

    paths = Paths.define('./blah/logs', {
        '{log_id}': {
            'model.h5': 'model',
            'model_spec.pkl': 'model_spec',
            'plots': {
                '{step_name}': {
                    '{plot_name}.png': 'plot'
                }
            }
        }
    })

    paths = paths.format(root='logs', log_id='adfasdfasdf', step_name='epoch_100')

    paths['model'] # logs/adfasdfasdf/model.h5
    paths['plot'] # logs/adfasdfasdf/plots/epoch_100/{plot_name}.png

    plot_files = glob.glob(paths['plots'].format(plot_name='*'))

    '''

    def __init__(self, paths, data=None):
        self._paths = paths
        self.data = {} if data is None else data

    @staticmethod
    def define(root, paths):
        '''Build paths from hierarchy'''
        data = {'root': root}
        return Paths({
            v: Path(*k, data=data)
            for k, v in get_keys({'{root}': paths})
        }, data)

    def __repr__(self):
        return '<Paths data={} \n{}\n>'.format(self.data, '\n'.join([
            '\t{} : {}'.format(name, self[name].maybe_format())
            for name in self._paths
        ]))

    def update(self, **kw):
        '''Update in place'''
        self.data.update(kw)
        for name in self._paths:
            self._paths.update(**kw)
        return self

    def specify(self, **kw):
        '''Return new Paths with added variables'''
        return Paths({
            name: self._paths[name].specify(**kw)
            for name in self._paths
        }, {**self.data, **kw})

    def format(self, **kw):
        return {
            name: self._paths[name].maybe_format(**kw)
            for name in self._paths
        }

    def partial_format(self, **kw):
        return {
            name: self._paths[name].partial_format(**kw)
            for name in self._paths
        }

    def __iter__(self):
        return iter(self._paths)

    def __getitem__(self, name):
        return self._paths[name]

    def get(self, name, **kw):
        '''Get a path with possibly'''
        return self._paths[name].specify(**kw)

    def parse(self, path, name):
        return self[name].parse(path)


class Path:
    '''



    '''
    def __init__(self, *path, data=None):
        self.path = os.path.join(*path)
        self.data = {} if data is None else data

    def __str__(self):
        '''Return path with all variables inserted. Will fail if variables are missing.
        There's no good way to do partial formatting - stackoverflow answers suck.
        '''
        # TODO: make print work - partial formatting is key !!
        return self.partial_format()

    def __repr__(self):
        return '<Path "{}" data={}>'.format(self.path, self.data)

    @property
    def str(self):
        return str(self)

    def update(self, **kw):
        self.data.update(**kw)

    def specify(self, **kw):
        return Path(self.path, data={**self.data, **kw})

    @property
    def fully_specified(self):
        try:
            self.format()
            return True
        except KeyError:
            return False

    def format(self, **kw):
        '''Works like string format.'''
        return self.path.format(**{**self.data, **kw})

    def parse(self, path):
        '''Extract variables from a compiled path'''
        from parse import parse
        r = parse(self.path, path)
        return r.fixed, r.named

    def maybe_format(self, **kw):
        p = self.specify(**kw)
        try:
            return p.format()
        except KeyError:
            return p

    def partial_format(self, **kw):
        return pformat(self.path, {**self.data, **kw})

    @property
    def glob_pattern(self):
        return gformat(self.path, self.data)

    @property
    def matching(self):
        return glob.glob(self.glob_pattern)


def get_keys(data, keys=None):
    keys = tuple(keys or ())
    for key, value in data.items():
        keys_ = keys + (key,)
        if isinstance(value, dict):
            for keys_, value in get_keys(value, keys_):
                yield keys_, value
        else:
            yield keys_, value
