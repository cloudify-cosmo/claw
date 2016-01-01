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
from path import path

from claw import configuration
from claw import tests
from claw.tests import resources


class BaseBootstrapTest(tests.BaseTestWithInit):

    def _test(self, reset=False):
        user = 'my_user'
        ip = 'my_host'
        key = 'my_key'
        configuration_name = 'conf'
        blueprint_dir = path(resources.DIR) / 'mock-manager-blueprint'
        blueprint_path = blueprint_dir / 'manager-blueprint.yaml'
        handler_configuration = {
            'manager_blueprint': str(blueprint_path)
        }
        suites_yaml = {
            'manager_blueprint_override_templates': {
                'mock_blueprint1': {
                    'node_templates.manager_configuration.type':
                        'cloudify.nodes.MyCloudifyManager'
                },
                'mock_blueprint2': {
                    'node_templates.manager_configuration.interfaces.'
                    'cloudify\.interfaces\.lifecycle.configure.implementation':
                        'configure.py'
                }
            },
            'inputs_override_templates': {
                'mock_inputs1': {
                    'user': user,
                    'key_filename': key,
                },
                'mock_inputs2': {
                    'ip': ip,
                    'rest_port': 80
                }
            },
            'handler_configurations': {
                configuration_name: handler_configuration
            }
        }
        self.settings.user_suites_yaml.write_text(yaml.safe_dump(suites_yaml))
        self.claw.bootstrap(configuration_name,
                            '-i', 'mock_inputs1',
                            '-i', 'mock_inputs2',
                            '-b', 'mock_blueprint1',
                            '-b', 'mock_blueprint2',
                            reset=reset)
        conf = configuration.Configuration(configuration_name)
        self.assertTrue(conf.cli_config['colors'])
        self.assertEqual(conf.handler_configuration['manager_ip'], ip)
        self.assertEqual(conf.handler_configuration['manager_user'], user)
        self.assertEqual(conf.handler_configuration['manager_key'], key)
        return configuration_name


class BootstrapTest(BaseBootstrapTest):

    def test_basic(self):
        self._test()

    def test_existing_configuration_no_reset(self):
        self._test()
        with self.assertRaises(sh.ErrorReturnCode):
            self._test()

    def test_existing_configuration_reset(self):
        self._test()
        self._test(reset=True)

    def test_no_such_configuration(self):
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.claw.bootstrap('no_such_configuration')
        self.assertIn('No such configuration', c.exception.stderr)
