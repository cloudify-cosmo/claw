import importlib
from contextlib import contextmanager

from cosmo_tester.framework import util


class ConfigurationPatcher(object):

    def __init__(self, obj):
        self.obj = obj

    @contextmanager
    def __getattr__(self, item):
        path = getattr(self.obj, '{0}_path'.format(item))
        with YamlPatcher(path, default_flow_style=False) as patch:
            yield patch


class YamlPatcher(util.YamlPatcher):

    def set_value(self, prop_path, new_value):
        obj, prop_name = self._get_parent_obj_prop_name_by_path(prop_path)
        if isinstance(new_value, dict) and new_value.get('func'):
            func_name = new_value['func']
            module, func = func_name.split(':')
            module = importlib.import_module(module)
            func = getattr(module, func)
            args = new_value.get('args', [])
            args.insert(0, obj.get(prop_name))
            kwargs = new_value.get('kwargs', {})
            obj[prop_name] = func(*args, **kwargs)
        else:
            super(YamlPatcher, self).set_value(prop_path, new_value)


# Some prebuilt functions
#########################

def filter_list(current_value, include):
    def is_included(_item):
        for included in include:
            if isinstance(included, basestring):
                if included in _item:
                    return True
            elif isinstance(included, dict):
                if all([value in _item[key]
                        for key, value in included.items()]):
                    return True
            else:
                raise NotImplementedError(str(included))
        return False
    return filter(is_included, current_value)


def filter_dict(current_value, exclude):
    return {k: v for k, v in current_value.items() if k not in exclude}
