import os
import pathtree as pt
import pytest

ROOT = os.path.join(os.path.dirname(__file__), 'data')

@pytest.fixture
def base_paths():
    return pt.tree('logs', {
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
        },
        'meta.json': 'meta',
    })

@pytest.fixture
def paths(base_paths):
    yield base_paths.specify(log_id='a')

@pytest.fixture
def paths_rw(base_paths):
    paths_rw = base_paths.specify(root=ROOT, log_id='a')
    yield paths_rw

    # Cleanup: paths.root.rmglob

    assert list(paths_rw.root.rglob())
    paths_rw.root.rmglob(include=True)
    assert not list(paths_rw.root.rglob())



def test_init():
    paths = pt.tree('logs', {'{log_id}': {'model.h5': 'model'}})
    assert paths.data['root'] == 'logs'
    assert set(paths.paths) == {'model', 'root'}

    paths = pt.tree({'plots', 'model.h5'})
    assert paths.data['root'] == '.'
    assert set(paths.paths) == {'plots', 'model.h5', 'root'}
    assert set(paths.format().values()) == {'./plots', './model.h5', '.'}

    paths = pt.tree('logsss', ['plots', 'model.h5'])
    assert paths.data['root'] == 'logsss'
    assert set(paths.paths) == {'plots', 'model.h5', 'root'}
    assert set(paths.format().values()) == {'logsss/plots', 'logsss/model.h5', 'logsss'}

    # legacy
    paths = pt.Paths.define('logs', {'{log_id}': {'model.h5': 'model'}})
    assert paths.data['root'] == 'logs'
    assert set(paths.paths) == {'model', 'root'}


def test_specify(base_paths):
    print(base_paths)
    # TODO: test Paths.add, Paths.get

    # Test: paths.get, getattr(paths, k)

    with pytest.raises(AttributeError):
        base_paths.log_id

    # Test: specify, unspecify

    paths = base_paths.specify(log_id='a')
    paths2 = paths.unspecify('log_id')
    print(paths.model, type(paths.model), type(paths.model._path))
    print(paths.model.unspecified)
    assert paths.model.unspecified.s == '{root}/{log_id}/model.h5'

    assert paths is not base_paths and paths2 is not paths
    assert 'log_id' in paths.data
    assert 'log_id' not in paths2.data
    assert not base_paths.fully_specified
    assert paths.specify(log_id=1, step_name=2, plot_name=3).fully_specified



def test_format(base_paths):
    # Test: format, partial_format, glob_pattern, glob

    paths = base_paths.specify(log_id='a')

    # convert to dict of strings
    pm = paths.model
    assert pm.fully_specified
    p = paths.format()

    # check Paths.format types
    assert isinstance(p['model'], str)
    assert isinstance(p['plot'], pt.Path)
    assert all(isinstance(p_, (str, pt.Path)) for p_ in p.values())
    assert all(isinstance(p_, (str, pt.Path)) for p_ in paths.partial_format().values())

    # check Paths.globs types
    assert isinstance(paths.globs(), list)

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
    p2 = paths.format(root='logs', log_id='b')
    assert p['model'] == 'logs/a/model.h5'
    assert p2['model_spec'] == 'logs/b/model_spec.pkl'

    # test in a loop
    plot_f = p['plot'].specify(step_name='epoch_100')
    print(repr(plot_f))
    for n in 'abcde':
        f = plot_f.format(plot_name=n)
        print(n, f)
        assert f == 'logs/a/plots/epoch_100/{}.png'.format(n)


def test_add(paths):
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


def test_parse(base_paths):
    paths = base_paths.specify(root='some/logs')

    expected = {
        'root': 'some/logs',
        'log_id': '12345',
        'step_name': '0002',
        'plot_name': 'f1_score',
    }

    # Test: parse, translate

    png_file = 'some/logs/12345/plots/0002/f1_score.png'
    jpg_file = 'some/logs/12345/plots/0002/f1_score.jpg'
    assert set(paths.plot.parse(png_file).items()) == set(expected.items())
    assert set(paths.parse(png_file, 'plot').items()) == set(expected.items())
    # assert paths.translate(png_file, 'plot', 'plot_jpg').format() == jpg_file
    assert paths.plot.translate(png_file, 'plot_jpg').format() == jpg_file
    assert paths.translate(png_file, 'plot', 'plot_jpg', use_data=False).format() == jpg_file

    with pytest.raises(ValueError):
        paths.plot.parse('broken/some/logs/12345/plots/0002/f1_score.png')
    # TODO: More intensive parse tests


def test_read_write(paths_rw):
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

    # Test: next_unique

    pmeta = paths_rw.meta
    assert not pmeta.exists() and pmeta.touch().exists()
    assert 'meta.json' in pmeta

    for i in range(5):
        pmeta_i = pt.Path(pmeta.next_unique(1))
        print(pmeta_i)
        assert not pmeta_i.exists()
        assert pmeta_i.touch().exists()
        assert 'meta.json' not in pmeta_i
        assert '{}.json'.format(i+1) in pmeta_i

    pmeta.rmglob()
    print(pmeta, pmeta.suffix('_*'), pmeta.suffix('_*').glob())
    pmeta.suffix('_*').rmglob()
    assert not pmeta.exists()
    assert not pmeta.suffix('_*').glob()


def test_misc():
    f = 'a/b/c'
    assert pt.path.fbase(f, 1) == 'b'
