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

import json

import sh

from systest import patcher
from systest import settings
from systest import tests
from systest.tests import resources


class ScriptTest(tests.BaseTestWithInit):

    def setUp(self):
        super(ScriptTest, self).setUp()
        self.systest.generate(tests.STUB_CONFIGURATION)

    def test_no_configuration(self):
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.systest.script('no_such_config', 'stub')
        self.assertIn('Not initialized', c.exception.stderr)

    def test_no_script_path(self):
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.systest.script(tests.STUB_CONFIGURATION, 'no_such_path')
        self.assertIn('locate no_such_path', c.exception.stderr)

    def test_no_script_func(self):
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self._test(script='')
        self.assertIn('Cannot find a function', c.exception.stderr)

    def test_script_in_script_dirs(self):
        scripts_dir = self.workdir / 'scripts'
        scripts_dir.mkdir()
        sett = settings.Settings()
        with patcher.YamlPatcher(sett.settings_path) as patch:
            patch.obj['scripts'] = [str(scripts_dir)]
        value = 'VALUE'
        script = "def script(): print '{}'".format(value)
        script_name = 'my_script.py'
        self._test(script=script, expected_output=value,
                   script_dir=scripts_dir,
                   script_name=script_name,
                   script_arg=script_name)

    def test_implicit_script_func_no_args(self):
        value = 'VALUE'
        script = "def script(): print '{}'".format(value)
        self._test(script=script, expected_output=value)

    def test_implicit_script_func_args(self):
        arg = 'ARG'
        script = "def script(arg): print arg"
        self._test(script=script, args=[arg], expected_output=arg)

    def test_explicit_script_func_no_args(self):
        func_name = 'foo'
        value = 'VALUE'
        script = "def {}(): print '{}'".format(func_name, value)
        self._test(script=script, args=[func_name], expected_output=value)

    def test_explicit_script_func_args(self):
        func_name = 'foo'
        arg = 'ARG'
        script = "def {}(arg): print arg".format(func_name)
        self._test(script=script, args=[func_name, arg], expected_output=arg)

    def test_conf_import(self):
        script = '''from systest import conf;
def script(): print conf.configuration'''
        self._test(script=script, expected_output=tests.STUB_CONFIGURATION)

    def test_argh_integration(self):
        script = resources.get('test_script_argh_integration.py')
        arg1 = 'arg1_value'
        arg2 = 'arg2_value'
        int_kwarg = '5'
        str_kwarg = 'str_kwarg_value'
        args = [
            arg1,
            arg2,
            '--int-kwarg', int_kwarg,
            '--boolean-flag',
            '--str-kwarg', str_kwarg
        ]
        output = self._test(script=script, args=args, skip_validation=True)
        output = json.loads(output)
        self.assertEqual(output, {
            'args': [arg1, arg2],
            'kwargs': {
                'boolean_flag': True,
                'int_kwarg': int(int_kwarg),
                'str_kwarg': str_kwarg
            }
        })

    def _test(self,
              script,
              args=None,
              expected_output=None,
              script_dir=None,
              script_name='script.py',
              script_arg=None,
              skip_validation=False):
        args = args or []
        script_dir = script_dir or self.workdir
        script_path = script_dir / script_name
        script_arg = script_arg or script_path
        script_path.write_text(script)
        output = self.systest.script(tests.STUB_CONFIGURATION,
                                     script_arg, *args).stdout.strip()
        if not skip_validation:
            self.assertEqual(output, expected_output)
        return output
