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
import uuid

import sh

from claw import patcher
from claw import tests
from claw.tests import resources


class ScriptTest(tests.BaseTestWithInit):

    def setUp(self):
        super(ScriptTest, self).setUp()
        self.claw.generate(tests.STUB_CONFIGURATION)

    def test_no_configuration(self):
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.claw.script('no_such_config', 'stub')
        self.assertIn('Not initialized', c.exception.stderr)

    def test_no_script_path(self):
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.claw.script(tests.STUB_CONFIGURATION, 'no_such_path')
        self.assertIn('locate no_such_path', c.exception.stderr)

    def test_no_script_func(self):
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self._test(script='')
        self.assertIn('Cannot find a function', c.exception.stderr)

    def test_script_in_script_dirs(self):
        scripts_dir1 = self.settings.default_scripts_dir
        scripts_dir2 = self.workdir / 'scripts2'
        scripts_dir2.mkdir()
        with patcher.YamlPatcher(self.settings.settings_path) as patch:
            patch.obj['scripts'] += [str(scripts_dir2)]
        for scripts_dir in [scripts_dir1, scripts_dir2]:
            gen_id = uuid.uuid4()
            value = 'VALUE-{0}'.format(gen_id)
            args = [value]
            expected = '{}-{}'.format(value, tests.STUB_CONFIGURATION)
            script = ("from claw import cosmo\n"
                      "def script(arg): print '{}-{}'.format(arg, "
                      "cosmo.configuration)")
            script_name = 'my-script-{0}.py'.format(gen_id)
            partial_script_name = script_name[:-3]
            for script_arg in [script_name, partial_script_name]:
                self._test(
                    script=script,
                    args=args,
                    expected_output=expected,
                    script_dir=scripts_dir,
                    script_name=script_name,
                    script_arg=script_arg,
                    also_run_as_built_in=script_arg == partial_script_name)

    def test_script_in_scripts_dir_name_conflict(self):
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self._test(script='', script_name='generate.py',
                       script_dir=self.settings.default_scripts_dir)
        self.assertIn('Name conflict', c.exception.stderr)
        self.assertIn('"generate"', c.exception.stderr)

    def test_script_in_scripts_dir_underscore_to_dash(self):
        self._test(script='def script(): print 123',
                   script_name='my_script.py',
                   script_dir=self.settings.default_scripts_dir,
                   expected_output='123',
                   script_arg='my_script',
                   also_run_as_built_in=True)

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
        script = '''from claw import cosmo;
def script(): print cosmo.configuration'''
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

    def test_script_logging(self):
        expected_in_once = 'ONE_TWO_THREE'
        expected_in = 'HELLO'
        expected_out = 'GOODBYE'
        script = '''import logging
from claw import cosmo
def script():
    cosmo.logger.info('{}')
    logging.warn('{}')
    logging.info('{}')'''.format(expected_in_once,
                                 expected_in,
                                 expected_out)
        output = self._test(script=script, skip_validation=True)
        self.assertIn(expected_in_once, output)
        self.assertEqual(1, output.count(expected_in_once))
        self.assertIn(expected_in, output)
        self.assertNotIn(expected_out, output)

    def _test(self,
              script,
              args=None,
              expected_output=None,
              script_dir=None,
              script_name='script.py',
              script_arg=None,
              skip_validation=False,
              also_run_as_built_in=False):
        args = args or []
        script_dir = script_dir or self.workdir
        script_path = script_dir / script_name
        script_arg = script_arg or script_path
        script_path.write_text(script)
        output = self.claw.script(tests.STUB_CONFIGURATION,
                                  script_arg, *args).stdout.strip()
        if not skip_validation:
            self.assertEqual(output, expected_output)
        if also_run_as_built_in:
            output = self.claw(script_arg.replace('_', '-'),
                               tests.STUB_CONFIGURATION,
                               *args).stdout.strip()
            if not skip_validation:
                self.assertEqual(output, expected_output)
        return output
