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

import os

import argh
import yaml
from path import path
from mock import patch

from systest import settings as _settings
from systest import tests


class TestSettings(tests.BaseTest):

    def setUp(self):
        super(TestSettings, self).setUp()
        self.settings = _settings.Settings()
        self.mock_suites_yaml = self.workdir / 'main_suites.yaml'
        self.mock_suites_yaml.touch()

    def test_default_settings_path(self):
        os.environ.pop(_settings.SYSTEST_SETTINGS, None)
        self.assertEqual(
            self.settings.settings_path,
            path(_settings.DEFAULT_SETTINGS_PATH).expanduser())

    def test_custom_settings_path(self):
        custom_path = 'SOME_PATH'
        with patch.dict(os.environ, {_settings.SYSTEST_SETTINGS: custom_path}):
            self.assertEqual(self.settings.settings_path, custom_path)

    def test_properties(self):
        self._write()
        self.assertEqual(self.settings.basedir, self.workdir)
        self.assertEqual(self.settings.configurations,
                         self.workdir / 'configurations')
        self.assertEqual(self.settings.user_suites_yaml,
                         self.workdir / 'suites.yaml')
        self.assertEqual(self.settings.blueprints_yaml,
                         self.workdir / 'blueprints.yaml')
        self.assertEqual(self.settings.main_suites_yaml,
                         self.mock_suites_yaml)
        self.assertEqual(self.settings.scripts, [])
        self.assertEqual(self.settings.settings, {
            'basedir': self.workdir.expanduser().abspath(),
            'main_suites_yaml': self.mock_suites_yaml.expanduser().abspath(),
            'scripts': []
        })

    def test_scripts(self):
        self._write()
        settings = yaml.safe_load(self.settings_path.text())
        dirs = [str(p) for p in [self.workdir / 'dir1', self.workdir / 'dir2']]
        settings['scripts'] = dirs
        self.settings_path.write_text(yaml.safe_dump(settings))
        self.assertEqual(self.settings.scripts, dirs)

    def test_no_settings(self):
        with self.assertRaises(argh.CommandError) as c:
            assert self.settings.settings
        self.assertIn('systest init', str(c.exception))

    def test_load_suites_yaml(self):
        self._write()
        (self.workdir / 'suites.yaml').write_text(yaml.safe_dump({
            'variables': {'a': 'A'},
            'key1': 'value1'
        }))
        self.mock_suites_yaml.write_text(yaml.safe_dump({
            'variables': {'b': 'B'},
            'key2': 'value2'
        }))
        self.assertEqual(self.settings.load_suites_yaml(),
                         {'key1': 'value1',
                          'variables': {'a': 'A', 'b': 'B'}})
        self.assertEqual(self.settings.load_suites_yaml(variables=True),
                         {'key1': 'value1',
                          'variables': {'a': 'A', 'b': 'B'}})
        self.assertEqual(self.settings.load_suites_yaml(variables=False),
                         {'key1': 'value1',
                          'variables': {'a': 'A'}})

    def test_load_blueprints_yaml(self):
        self.test_load_suites_yaml()
        (self.workdir / 'blueprints.yaml').write_text(yaml.safe_dump({
            'variables': {'c': 'C'},
            'key3': 'value3'
        }))
        self.assertEqual(self.settings.load_blueprints_yaml(),
                         {'key3': 'value3',
                          'variables': {'a': 'A', 'b': 'B', 'c': 'C'}})
        self.assertEqual(self.settings.load_blueprints_yaml(variables=True),
                         {'key3': 'value3',
                          'variables': {'a': 'A', 'b': 'B', 'c': 'C'}})
        self.assertEqual(self.settings.load_blueprints_yaml(variables=False),
                         {'key3': 'value3',
                          'variables': {'c': 'C'}})

    def _write(self):
        self.settings.write_settings(self.workdir,
                                     self.mock_suites_yaml)
