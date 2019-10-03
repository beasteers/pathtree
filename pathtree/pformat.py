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


class Field:
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
