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

from systest import configuration
from systest import settings
from systest import tests


class GenerateBlueprintTest(tests.BaseTest):

    def setUp(self):
        super(GenerateBlueprintTest, self).setUp()
        self.inputs = {'some': 'input'}
        self.variables = {'a': 'AAA', 'b': 'BBB'}

    def test_basic(self):
        self._test()

    def test_inputs(self):
        self._test(inputs=self.inputs)

    def test_inputs_override_in_blueprint_configuration_with_inputs(self):
        self._test_inputs_override_in_blueprint_configuration(
            inputs=self.inputs)

    def test_inputs_override_in_blueprint_configuration_no_inputs(self):
        self._test_inputs_override_in_blueprint_configuration()

    def _test_inputs_override_in_blueprint_configuration(self, inputs=None):
        inputs_override = {'override': 'inputs {{a}}'}
        processed_inputs_override = {'override': 'inputs AAA'}
        self._test(inputs=inputs,
                   inputs_override=inputs_override,
                   processed_inputs_override=processed_inputs_override)

    def test_blueprint_override_in_blueprint_configuration(self):
        blueprint_override = {'override': 'blueprint {{a}}'}
        processed_blueprint_override = {'override': 'blueprint AAA'}
        self._test(inputs=self.inputs,
                   blueprint_override=blueprint_override,
                   processed_blueprint_override=processed_blueprint_override)

    def test_properties_in_variables(self):
        properties = {'some_property': 'some_value'}
        inputs_override = {'override': 'inputs {{properties.some_property}}'}
        processed_inputs_override = {'override': 'inputs some_value'}
        self._test(inputs_override=inputs_override,
                   processed_inputs_override=processed_inputs_override,
                   properties=properties)

    def test_existing_blueprint_no_reset(self):
        self._test()
        with self.assertRaises(sh.ErrorReturnCode):
            self._test(skip_conf_generate=True)

    def test_existing_blueprint_reset(self):
        self._test()
        self._test(reset=True, skip_conf_generate=True)

    def test_no_configuration(self):
        self.init()
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.systest('generate-blueprint', 'no_such_configuration',
                         tests.STUB_BLUEPRINT)
        self.assertIn('Not initialized', c.exception.stderr)

    def _test(self,
              inputs=None,
              inputs_override=None,
              processed_inputs_override=None,
              blueprint_override=None,
              processed_blueprint_override=None,
              properties=None,
              reset=False,
              skip_conf_generate=False):
        configuration_name = 'conf1'
        blueprint_name = 'blueprint1'
        properties_name = 'some_properties'

        if not skip_conf_generate:
            main_suites_yaml = {
                'handler_properties': {
                    properties_name: properties or {}
                }
            }
            main_suites_yaml_path = self.workdir / 'main-suites.yaml'
            main_suites_yaml_path.write_text(yaml.safe_dump(main_suites_yaml))
            self.init(main_suites_yaml_path)

        conf = configuration.Configuration(configuration_name)
        blueprint_dir = self.workdir / 'blueprint'
        blueprint_dir.mkdir_p()
        manager_blueprint_path = blueprint_dir / 'manager-blueprint.yaml'
        inputs_path = blueprint_dir / 'inputs.yaml'
        blueprint_path = blueprint_dir / 'some-blueprint.yaml'
        new_blueprint_dir = conf.dir / 'blueprints' / blueprint_name
        new_inputs_path = new_blueprint_dir / 'inputs.yaml'
        new_blueprint_path = (new_blueprint_dir / 'blueprint' /
                              'blueprint.yaml')
        blueprint_configuration_path = (new_blueprint_dir /
                                        'blueprint-configuration.yaml')

        manager_blueprint = {'some': 'manager_blueprint'}
        blueprint = {'some_user': 'blueprint_content'}

        if inputs:
            inputs_path.write_text(yaml.safe_dump(inputs))
        blueprint_path.write_text(yaml.safe_dump(blueprint))
        manager_blueprint_path.write_text(yaml.safe_dump(manager_blueprint))

        blueprint_configuration = {
            'blueprint': str(blueprint_path)
        }

        if inputs:
            blueprint_configuration['inputs'] = str(inputs_path)
        if inputs_override:
            blueprint_configuration['inputs_override'] = inputs_override
        if blueprint_override:
            blueprint_configuration['blueprint_override'] = blueprint_override

        user_suites_yaml = {
            'handler_configurations': {
                configuration_name: {
                    'manager_blueprint': str(manager_blueprint_path),
                    'properties': properties_name
                }
            }
        }
        blueprints_yaml = {
            'variables': self.variables,
            'blueprints': {
                blueprint_name: blueprint_configuration
            }
        }
        sett = settings.Settings()
        sett.user_suites_yaml.write_text(yaml.safe_dump(user_suites_yaml))
        sett.blueprints_yaml.write_text(yaml.safe_dump(blueprints_yaml))

        if not skip_conf_generate:
            self.systest.generate(configuration_name)
        self.systest('generate-blueprint', configuration_name,
                     blueprint_name, reset=reset)

        expected_inputs = (inputs or {}).copy()
        expected_inputs.update((processed_inputs_override or {}))
        self.assertEqual(expected_inputs,
                         yaml.safe_load(new_inputs_path.text()))

        expected_blueprint = blueprint.copy()
        expected_blueprint.update((processed_blueprint_override or {}))
        self.assertEqual(expected_blueprint,
                         yaml.safe_load(new_blueprint_path.text()))

        expected_blueprint_configuration = blueprint_configuration.copy()
        expected_blueprint_configuration.pop('inputs_override', {})
        expected_blueprint_configuration.pop('blueprint_override', {})
        expected_blueprint_configuration.update({
            'blueprint': new_blueprint_path,
            'inputs': new_inputs_path
        })
        self.assertEqual(expected_blueprint_configuration,
                         yaml.safe_load(blueprint_configuration_path.text()))
        self.assertEqual(blueprints_yaml,
                         yaml.safe_load(sett.blueprints_yaml.text()))
