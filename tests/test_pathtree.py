import os
import pathtree as pt
import pytest


def test_paths():
    # TODO: test Paths.add, Paths.get

    ROOT = os.path.join(os.path.dirname(__file__), 'data')

    # Test: tree, Paths.define

    paths = pt.Paths.define('logs', {'{log_id}': {}})
    paths = pt.tree('logs', {
        '{log_id}': {
            'model.h5': 'model',
            'model_spec.pkl': 'model_spec',
            'plots': {
                '{step_name}': {
                    '{plot_name}.png': 'plot',
                    '{plot_name}.jpg': 'plot_jpg',
                }
            },
            'results': {'{step_name}.csv': 'result_step'},
            'models': {'{step_name}.h5': 'model_step'},
        }
    })
    print(paths)

    # Test: paths.get, getattr(paths, k)

    with pytest.raises(AttributeError):
        paths.log_id

    # Test: specify, unspecify

    paths_ = paths.specify(log_id='a')
    paths_2 = paths_.unspecify('log_id')
    print(paths_.model, type(paths_.model), type(paths_.model._path))
    print(paths_.model.unspecified)
    assert paths_.model.unspecified.s == '{root}/{log_id}/model.h5'

    assert paths_ is not paths and paths_2 is not paths_
    assert 'log_id' in paths_.data
    assert 'log_id' not in paths_2.data
    assert not paths.fully_specified
    assert paths.specify(log_id=1, step_name=2, plot_name=3).fully_specified

    # Test: Paths.add

    # when you don't have a pre-named node
    paths_add = paths.add(paths.model_step.up(), {
        '': 'model_step_dir',
        '{step_name}-2.h5': 'model_step2',
    })
    print(paths_add)
    assert paths_add.model_step2.path_pattern == '{root}/{log_id}/models/{step_name}-2.h5'

    # when you do have a pre-named node
    paths_add = paths.add('model_step_dir', {
        '{step_name}-3.h5': 'model_step3',
    })
    print(paths_add)
    assert paths_add.model_step3.path_pattern == '{root}/{log_id}/models/{step_name}-3.h5'

    # when you want to add an existing path with a new root
    paths_node = pt.tree({
        '{step_name}-4.h5': 'model_step4',
    })
    paths_add = paths.add('model_step_dir', paths_node)
    print(paths_add)
    assert paths_add.model_step4.path_pattern == '{root}/{log_id}/models/{step_name}-4.h5'

    # Test: format, partial_format, glob_pattern, glob

    # convert to dict of strings
    pm = paths_.model
    assert pm.fully_specified
    p = paths_.format()

    # check Paths.format types
    assert isinstance(p['model'], str)
    assert isinstance(p['plot'], pt.Path)
    assert all(isinstance(p_, (str, pt.Path)) for p_ in p.values())
    assert all(isinstance(p_, (str, pt.Path)) for p_ in paths_.partial_format().values())

    # check Paths.globs types
    assert isinstance(paths_.globs(), list)

    # test fully specified strings have been formatted
    assert pm.s == p['model']
    assert p['model'] == 'logs/a/model.h5'
    assert p['model_spec'] == 'logs/a/model_spec.pkl'

    pm_2 = pm.unspecify('log_id')
    assert not pm_2.fully_specified

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
    paths_p = paths.specify(root='some/logs')

    expected = {
        'root': 'some/logs',
        'log_id': '12345',
        'step_name': '0002',
        'plot_name': 'f1_score',
    }

    # Test: parse, translate

    png_file = 'some/logs/12345/plots/0002/f1_score.png'
    jpg_file = 'some/logs/12345/plots/0002/f1_score.jpg'
    assert set(paths_p.plot.parse(png_file).items()) == set(expected.items())
    assert set(paths_p.parse(png_file, 'plot').items()) == set(expected.items())
    # assert paths.translate(png_file, 'plot', 'plot_jpg').format() == jpg_file
    assert paths_p.plot.translate(png_file, 'plot_jpg').format() == jpg_file
    assert paths.translate(png_file, 'plot', 'plot_jpg', use_data=False).format() == jpg_file

    with pytest.raises(ValueError):
        paths_p.plot.parse('broken/some/logs/12345/plots/0002/f1_score.png')
    # TODO: More intensive parse tests

    paths_rw = paths_.specify(root=ROOT)
    pm = paths_rw.specify(step_name='step_nonexistant').model_step

    paths_rw.makedirs()
    assert pm.up().exists()
    paths_rw.root.rmglob(include=True)
    assert not pm.up().exists()

    pm.find_sibling('plot')
    with pytest.raises(KeyError):
        pm.find_sibling('plot1234')

    p_blank = pt.Path()
    with pytest.raises(AttributeError):
        p_blank.find_sibling('plot1234')

    # Test: read, write, up, exists

    text = 'adsfasdfasdf'
    pm.write(text)
    assert pm.exists()
    assert pm.read() == text


    # Test: rm, rmglob

    pm.rm()
    assert pm.up().exists() and not pm.exists()
    pm.up().rmglob()
    assert pm.up().exists()
    pm.up().rmglob(include=True)
    assert not pm.up().exists()
    pm.touch()
    assert pm.exists()

    # Cleanup: paths.root.rmglob

    assert list(paths_rw.root.rglob())
    paths_rw.root.rmglob(include=True)
    assert not list(paths_rw.root.rglob())


def test_misc():
    f = 'a/b/c'
    assert pt.path.fbase(f, 1) == 'b'
