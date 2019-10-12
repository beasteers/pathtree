import string

__all__ = ['pformat', 'gformat']

class PartialFormatter(string.Formatter):
    '''Partial string formatting!! Finally!
    >>> f = lambda x, *a, **kw: (x, pformat(x, *a, **kw))

    >>> print(f('{a}/b/{c}/d/{e}',          e='eee'))
    ... print(f('{a:s}/b/{c!s:s}/d/{e}',    e='eee'))
    ... print(f('{}/b/{}/d/{}',             'aaa', 'ccc'))
    ... print(f('{:s}/b/{}/d/{:s}',         'aaa', 'ccc'))

    ('{a}/b/{c}/d/{e}', '{a}/b/{c}/d/eee')
    ('{}/b/{}/d/{}', 'aaa/b/ccc/d/{}')
    ('{a:s}/b/{c!s:s}/d/{e}', '{a:s}/b/{c!s:s}/d/eee')
    ('{:s}/b/{}/d/{:s}', 'aaa/b/ccc/d/{:s}')

    '''
    def get_field(self, key, a, kw):
        try:
            return super().get_field(key, a, kw)
        except KeyError:
            return Field(key), key
        except IndexError:
            # this will drop any format indices
            return Field(), key

    def convert_field(self, obj, conversion):
        if isinstance(obj, Field):
            obj.conv = conversion
            return obj
        return super().convert_field(obj, conversion)

    def format_field(self, obj, format_spec):
        if isinstance(obj, Field):
            obj.spec = format_spec
            return obj.field
        return super().format_field(obj, format_spec)




class GlobFormatter(string.Formatter):
    '''File path formatting

    For any missing keys, an asterisk will be inserted.

    This is necessary for any fields where non-string format specifiers
    are used. For example:

    `'logs/epoch_{i_epoch:04f}'.format(i_epoch='*')`

    This will fail because `:04f` is an invalid formatter for `'*'`.

    '''
    def get_field(self, key, a, kw):
        try:
            return super().get_field(key, a, kw)
        except (KeyError, IndexError):
            return Field(value='*'), key

    def convert_field(self, obj, conversion):
        if isinstance(obj, Field):
            return obj
        return super().convert_field(obj, conversion)

    def format_field(self, obj, format_spec):
        if isinstance(obj, Field):
            return obj.value
        return super().format_field(obj, format_spec)



class RegexFormatter(string.Formatter):
    '''Regex match formatting
    Make sure that a string matches a regular expression before inserting.

    Example
    -------
    >>> rformat('{i:/\d[^\d]*/}', i='3aasdfasdf')
    '3aasdfasdf'
    >>> rformat('{i:/\d[^\d]*/}', i='a3aasdfasdf')
    ---------------------------------------------------------------------------
    ValueError                                Traceback (most recent call last)
    ...
    ValueError: Input (a3aasdfasdf) did not match the regex pattern (/\d[^\d]*/)
    '''
    def format_field(self, obj, format_spec):
        import re
        if format_spec.startswith('/') and format_spec.endswith('/'):
            obj = str(obj) # coerce to string for re
            if re.match(format_spec[1:-1], obj):
                return obj

            raise ValueError(
                'Input ({}) did not match the regex pattern ({})'.format(
                    obj, format_spec))
        return super().format_field(obj, format_spec)



def _try_all(func, collection='children'):
    def inner(self, *a, **kw):
        objs = list(getattr(self, collection)) + [self]
        e = Exception('Error thrown in {}.{}'.format(self, func.__name__))
        for o in objs:
            try:
                return getattr(o, func.__name__)(*a, **kw)
            except Exception as e:
                continue
        raise e
    return inner

class MultiFormatter(string.Formatter):
    # TODO: this is only a sketch
    '''Use multiple format rules with fallback'''
    def __init__(self, *children):
        self.children = children

    get_field = _try_all(string.Formatter.get_field, 'children')
    convert_field = _try_all(string.Formatter.convert_field, 'children')
    format_field = _try_all(string.Formatter.format_field, 'children')



class Field:
    '''This is used to mark a field of interest.'''
    def __init__(self, key=None, conv=None, spec=None, value=None):
        self.key, self.conv, self.spec, self.value = (
            key, conv, spec, value)

    @property
    def field(self):
        return ('{' + (
            (self.key or '') +
            ('!' + self.conv if self.conv else '') +
            (':' + self.spec if self.spec else '')
        ) + '}')


pformat = PartialFormatter().format
gformat = GlobFormatter().format
