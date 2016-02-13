########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
############

import copy
import importlib
import os

from cosmo_tester.framework import util


class YamlPatcher(util.YamlPatcher):

    def set_value(self, prop_path, new_value):
        obj, prop_name = self._get_parent_obj_prop_name_by_path(prop_path)
        if isinstance(new_value, dict) and new_value.get('func'):
            func_name = new_value['func']
            module, func = func_name.split(':')
            module = importlib.import_module(module)
            func = getattr(module, func)
            args = copy.copy(new_value.get('args', []))
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
                if all([value in (_item.get(key) or '')
                        for key, value in included.items()]):
                    return True
            else:
                raise NotImplementedError(str(included))
        return False
    return filter(is_included, current_value)


def filter_dict(current_value, exclude):
    return {k: v for k, v in current_value.items() if k not in exclude}


def env(current_value, key, default=None):
    return os.environ.get(key, default)
