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

import sh
import yaml

from systest import settings
from systest import tests


class GenerateTest(tests.BaseTestWithInit):

    def setUp(self):
        super(GenerateTest, self).setUp()
        self.inputs = {'some': 'input'}
        self.variables = {'a': 'AAA', 'b': 'BBB'}

    def test_basic(self):
        self._test()

    def test_inputs(self):
        self._test(inputs=self.inputs)

    def test_inputs_override_in_handler_configuration_with_inputs(self):
        self._test_inputs_override_in_handler_configuration(inputs=self.inputs)

    def test_inputs_override_in_handler_configuration_no_inputs(self):
        self._test_inputs_override_in_handler_configuration()

    def _test_inputs_override_in_handler_configuration(self, inputs=None):
        inputs_override = {'override': 'inputs {{a}}'}
        processed_inputs_override = {'override': 'inputs AAA'}
        self._test(inputs=inputs,
                   inputs_override=inputs_override,
                   processed_inputs_override=processed_inputs_override)

    def test_manager_blueprint_override_in_handler_configuration(self):
        blueprint_override = {'override': 'blueprint {{a}}'}
        processed_blueprint_override = {'override': 'blueprint AAA'}
        self._test(inputs=self.inputs,
                   blueprint_override=blueprint_override,
                   processed_blueprint_override=processed_blueprint_override)

    def test_inputs_override_in_command_line_no_handler_inputs_override(self):
        self._test_inputs_override_in_command_line()

    def test_inputs_override_in_command_line_with_handler_inputs_override(self):  # noqa
        inputs_override = {'override': 'inputs {{a}}'}
        processed_inputs_override = {'override': 'inputs AAA'}
        self._test_inputs_override_in_command_line(
            handler_inputs_override=inputs_override,
            processed_handler_inputs_override=processed_inputs_override)

    def _test_inputs_override_in_command_line(
            self,
            handler_inputs_override=None,
            processed_handler_inputs_override=None):  # noqa
        cmd_inputs_override = {
            'from_cmd1': {'cmd_override': 'cmd_inputs {{b}}'},
            'from_cmd2': {'cmd_override2': 'cmd_inputs2 {{b}}'}
        }
        processed_inputs_override = {'cmd_override': 'cmd_inputs BBB',
                                     'cmd_override2': 'cmd_inputs2 BBB'}
        if processed_handler_inputs_override:
            processed_inputs_override.update(processed_handler_inputs_override)
        self._test(inputs_override=handler_inputs_override,
                   cmd_inputs_override=cmd_inputs_override,
                   processed_inputs_override=processed_inputs_override)

    def test_manager_blueprint_override_in_command_line_no_handler_blueprint_override(self):  # noqa
        self._test_manager_blueprint_override_in_command_line()

    def test_manager_blueprint_override_in_command_line_with_handler_blueprint_override(self):  # noqa
        blueprint_override = {'override': 'blueprint {{a}}'}
        processed_blueprint_override = {'override': 'blueprint AAA'}
        self._test_manager_blueprint_override_in_command_line(
            handler_blueprint_override=blueprint_override,
            processed_handler_blueprint_override=processed_blueprint_override)

    def _test_manager_blueprint_override_in_command_line(
            self,
            handler_blueprint_override=None,
            processed_handler_blueprint_override=None):  # noqa
        cmd_blueprint_override = {
            'from_cmd1': {'cmd_override': 'cmd_blueprint {{b}}'},
            'from_cmd2': {'cmd_override2': 'cmd_blueprint2 {{b}}'}
        }
        processed_blueprint_override = {'cmd_override': 'cmd_blueprint BBB',
                                        'cmd_override2': 'cmd_blueprint2 BBB'}
        if processed_handler_blueprint_override:
            processed_blueprint_override.update(
                processed_handler_blueprint_override)
        self._test(blueprint_override=handler_blueprint_override,
                   cmd_blueprint_override=cmd_blueprint_override,
                   processed_blueprint_override=processed_blueprint_override)

    def test_no_such_configuration(self):
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.systest.generate('no_such_configuration')
        self.assertIn('No such configuration', c.exception.stderr)

    def test_existing_configuration_no_reset(self):
        self._test()
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self._test()
        self.assertIn('Already initialized', c.exception.stderr)

    def test_existing_configuration_reset(self):
        self._test()
        self._test(reset=True)

    def test_existing_current_configuration(self):
        self._test()
        self._test(configuration='some_other_conf')

    def _test(self,
              inputs=None,
              inputs_override=None,
              cmd_inputs_override=None,
              processed_inputs_override=None,
              blueprint_override=None,
              cmd_blueprint_override=None,
              processed_blueprint_override=None,
              reset=False,
              configuration=None):
        configuration = configuration or 'conf1'
        blueprint_dir = self.workdir / 'blueprint'
        blueprint_dir.mkdir_p()
        inputs_path = blueprint_dir / 'inputs.yaml'
        blueprint_path = blueprint_dir / 'some-manager-blueprint.yaml'

        config_dir = self.workdir / 'configurations' / configuration
        new_inputs_path = config_dir / 'inputs.yaml'
        new_blueprint_path = (config_dir / 'manager-blueprint' /
                              'manager-blueprint.yaml')
        handler_configuration_path = config_dir / 'handler-configuration.yaml'

        blueprint = {'some_other': 'manager_blueprint'}

        if inputs:
            inputs_path.write_text(yaml.safe_dump(inputs))
        blueprint_path.write_text(yaml.safe_dump(blueprint))

        handler_configuration = {
            'handler': 'stub_handler',
            'manager_blueprint': str(blueprint_path),
        }

        if inputs:
            handler_configuration['inputs'] = str(inputs_path)
        if inputs_override:
            handler_configuration['inputs_override'] = inputs_override
        if blueprint_override:
            handler_configuration[
                'manager_blueprint_override'] = blueprint_override

        command_args = [configuration]

        suites_yaml = {
            'variables': self.variables,
            'handler_configurations': {
                configuration: handler_configuration
            }
        }
        if cmd_inputs_override:
            suites_yaml['inputs_override_templates'] = cmd_inputs_override
            for name in cmd_inputs_override:
                command_args += ['-i', name]
        if cmd_blueprint_override:
            suites_yaml['manager_blueprint_override_templates'] = (
                cmd_blueprint_override)
            for name in cmd_blueprint_override:
                command_args += ['-b', name]

        sett = settings.Settings()
        sett.user_suites_yaml.write_text(yaml.safe_dump(suites_yaml))

        self.systest.generate(*command_args, reset=reset)

        expected_inputs = (inputs or {}).copy()
        expected_inputs.update((processed_inputs_override or {}))
        self.assertEqual(expected_inputs,
                         yaml.safe_load(new_inputs_path.text()))

        expected_blueprint = blueprint.copy()
        expected_blueprint.update((processed_blueprint_override or {}))
        self.assertEqual(expected_blueprint,
                         yaml.safe_load(new_blueprint_path.text()))

        expected_handler_configuration = handler_configuration.copy()
        expected_handler_configuration.pop('inputs_override', {})
        expected_handler_configuration.pop('manager_blueprint_override', {})
        expected_handler_configuration.update({
            'install_manager_blueprint_dependencies': False,
            'manager_blueprint': new_blueprint_path,
            'inputs': new_inputs_path
        })
        self.assertEqual(expected_handler_configuration,
                         yaml.safe_load(handler_configuration_path.text()))
        self.assertEqual(suites_yaml,
                         yaml.safe_load(sett.user_suites_yaml.text()))
        self.assertEqual((self.workdir / 'configurations' / '+').readlink(),
                         configuration)
