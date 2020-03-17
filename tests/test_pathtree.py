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
    print(paths)

    # test specify/unspecify
    paths_ = paths.specify(root='logs', log_id='a')
    paths_2 = paths_.unspecify('log_id')

    assert paths_ is not paths and paths_2 is not paths_
    assert 'log_id' in paths_.data
    assert 'log_id' not in paths_2.data

    # convert to dict of strings
    p = paths_.format()

    # test fully specified strings have been formatted
    assert p['model'] == 'logs/a/model.h5'
    assert p['model_spec'] == 'logs/a/model_spec.pkl'

    # test underspecified paths have not
    assert isinstance(p['plot'], pt.Path)
    assert p['plot'].partial_format() == 'logs/a/plots/{step_name}/{plot_name}.png'
    assert p['plot'].glob_pattern == 'logs/a/plots/*/*.png'
    assert isinstance(p['plot'].glob(), list)
    assert tuple(sorted(list(p['plot'].iglob()))) == tuple(p['plot'].glob())

    # test that format kw are different
    p2 = paths_.format(root='logs', log_id='b')
    assert p['model'] == 'logs/a/model.h5'
    assert p2['model_spec'] == 'logs/b/model_spec.pkl'

    # test in a loop
    plot_f = p['plot'].specify(step_name='epoch_100')
    print(repr(plot_f))
    for n in 'abcde':
        f = plot_f.format(plot_name=n)
        print(n, f)
        assert f == 'logs/a/plots/epoch_100/{}.png'.format(n)

    # test parsing
    plot_file = paths.plot.specify(root='some/logs')

    expected = {
        'root': 'some/logs',
        'log_id': '12345',
        'step_name': '0002',
        'plot_name': 'f1_score',
    }

    plot_data = plot_file.parse('some/logs/12345/plots/0002/f1_score.png')
    assert set(plot_data.items()) == set(expected.items())
    plot_data = plot_file.parse('some/logs/12345/plots/0002/f1_score.png')
    assert set(plot_data.items()) == set(expected.items())

def test_formatter():
    assert pt.pformat('{a}/b/{c}/d/{e}', e='eee') == '{a}/b/{c}/d/eee'
    assert pt.pformat('{a:s}/b/{c!s:s}/d/{e}', e='eee') == '{a:s}/b/{c!s:s}/d/eee'
    assert pt.pformat('{}/b/{}/d/{}', 'aaa', 'ccc') == 'aaa/b/ccc/d/{}'
    assert pt.pformat('{:s}/b/{}/d/{:s}', 'aaa', 'ccc') == 'aaa/b/ccc/d/{:s}'
    assert pt.gformat('{:s}/b/{}/d/{:s}', 'aaa', 'ccc') == 'aaa/b/ccc/d/*'
