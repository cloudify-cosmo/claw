import yaml

from systest import patcher
from systest import tests


class TestPatcher(tests.BaseTest):

    def setUp(self):
        super(TestPatcher, self).setUp()
        self.yaml_path = self.workdir / 'test.yaml'

    def test_derived_set_value(self):
        test_yaml = {'a': 'A'}
        self.write_yaml(test_yaml)
        with patcher.YamlPatcher(self.yaml_path) as patch:
            patch.set_value('b', 'B')
        self.assertEqual(self.read_yaml(),
                         {'a': 'A', 'b': 'B'})

    def test_set_value_no_current_value(self):
        self.write_yaml({})
        with patcher.YamlPatcher(self.yaml_path) as patch:
            patch.set_value('b.c', {
                'func': '{0}:func_no_current_value'.format(__name__)
            })
        self.assertEqual(self.read_yaml()['b']['c'],
                         func_no_current_value(None))

    def test_set_value_current_value(self):
        current_value = 'A'
        self.write_yaml({'a': current_value})
        with patcher.YamlPatcher(self.yaml_path) as patch:
            patch.set_value('a', {
                'func': '{0}:func_current_value'.format(__name__)
            })
        self.assertEqual(self.read_yaml()['a'],
                         func_current_value(current_value))

    def test_set_value_args_and_kwargs(self):
        current_value = 'A'
        args = [1, 2, 3]
        kwargs = {'one': 'ONE', 'two': 'TWO'}
        self.write_yaml({'a': 'A'})
        with patcher.YamlPatcher(self.yaml_path) as patch:
            patch.set_value('a', {
                'func': '{0}:func_args_and_kwargs'.format(__name__),
                'args': args,
                'kwargs': kwargs
            })
        self.assertEqual(self.read_yaml()['a'],
                         [current_value, args, kwargs])

    def test_builtin_filter_list_string_list(self):
        test_yaml = {
            'a': ['string one', 'string two', 'string three']
        }
        self.write_yaml(test_yaml)
        with patcher.YamlPatcher(self.yaml_path) as patch:
            patch.set_value('a', {
                'func': 'systest.patcher:filter_list',
                'kwargs': {'include': ['one', 'two']}
            })
        self.assertEqual(self.read_yaml()['a'], ['string one', 'string two'])

    def test_builtin_filter_list_dict_list(self):
        test_yaml = {
            'a': [{'key1': 'string value11'},
                  {'key1': 'string value12', 'key2': 'string value22'},
                  {'key1': 'string value13', 'key2': 'string value23'}]
        }
        self.write_yaml(test_yaml)
        with patcher.YamlPatcher(self.yaml_path) as patch:
            patch.set_value('a', {
                'func': 'systest.patcher:filter_list',
                'kwargs': {'include': [{'key1': 'value12', 'key2': 'value22'},
                                       {'key1': 'value11'}]}
            })
        self.assertEqual(
            self.read_yaml()['a'],
            [{'key1': 'string value11'},
             {'key1': 'string value12', 'key2': 'string value22'}])

    def test_builtin_filter_dict(self):
        test_yaml = {
            'a': {
                'a1': 1,
                'a2': 2,
                'a3': 3
            }
        }
        self.write_yaml(test_yaml)
        with patcher.YamlPatcher(self.yaml_path) as patch:
            patch.set_value('a', {
                'func': 'systest.patcher:filter_dict',
                'kwargs': {'exclude': ['a3']}
            })
        self.assertEqual(self.read_yaml()['a'],
                         {'a1': 1, 'a2': 2})

    def write_yaml(self, obj):
        self.yaml_path.write_text(yaml.safe_dump(obj))

    def read_yaml(self):
        return yaml.safe_load(self.yaml_path.text())


def func_no_current_value(current_value):
    assert not current_value
    return 'value'


def func_current_value(current_value):
    assert current_value
    return current_value * 2


def func_args_and_kwargs(current_value, *args, **kwargs):
    return current_value, args, kwargs
