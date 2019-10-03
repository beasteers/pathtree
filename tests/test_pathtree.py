import glob
import pathtree as pt


def test_paths():
    paths = pt.Paths.define('./blah/logs', {
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
    print(paths['plot'].matching)

    p2 = paths.format(root='logs', log_id='b')
    assert p['model'] == 'logs/a/model.h5'
    assert p2['model_spec'] == 'logs/b/model_spec.pkl'

    plot_f = p['plot'].specify(step_name='epoch_100')
    print(repr(plot_f))
    for n in 'abcde':
        f = plot_f.format(plot_name=n)
        print(n, f)
        assert f == 'logs/a/plots/epoch_100/{}.png'.format(n)

    plot_files = glob.glob(plot_f.format(plot_name='*'))
    print(plot_files)


def test_formatter():
    assert pt.pformat('{a}/b/{c}/d/{e}', e='eee') == '{a}/b/{c}/d/eee'
    assert pt.pformat('{a:s}/b/{c!s:s}/d/{e}', e='eee') == '{a:s}/b/{c!s:s}/d/eee'
    assert pt.pformat('{}/b/{}/d/{}', 'aaa', 'ccc') == 'aaa/b/ccc/d/{}'
    assert pt.pformat('{:s}/b/{}/d/{:s}', 'aaa', 'ccc') == 'aaa/b/ccc/d/{:s}'
    assert pt.gformat('{:s}/b/{}/d/{:s}', 'aaa', 'ccc') == 'aaa/b/ccc/d/*'
