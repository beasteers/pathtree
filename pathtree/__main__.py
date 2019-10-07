from . import *

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

paths = paths.specify(root='logs', log_id='a')
print(paths)

p = paths.format()

print(p)
print(p['model'], p['model_spec'])
assert p['model'] == 'logs/a/model.h5'
assert p['model_spec'] == 'logs/a/model_spec.pkl'

print(paths['plot'].partial_format())
print(paths['plot'].glob_pattern)
print(paths['plot'].matching_files)

p2 = paths.format(root='logs', log_id='b')
assert p['model'] == 'logs/a/model.h5'
assert p2['model_spec'] == 'logs/b/model_spec.pkl'
# assert paths['plot'] == 'logs/adfasdfasdf/plots/epoch_100/{plot_name}.png'

plot_f = p['plot'].specify(step_name='epoch_100')
for n in 'abcde':
    f = plot_f.format(plot_name=n)
    print(n, f)
    assert f == 'logs/a/plots/epoch_100/{}.png'.format(n)

f = lambda x, *a, **kw: (x, pformat(x, *a, **kw))

print(f('{a}/b/{c}/d/{e}', e='eee'))
print(f('{}/b/{}/d/{}', 'aaa', 'ccc'))
print(f('{a:s}/b/{c!s:s}/d/{e}', e='eee'))
print(f('{:s}/b/{}/d/{:s}', 'aaa', 'ccc'))
