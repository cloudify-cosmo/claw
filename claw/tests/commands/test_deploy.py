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

import bottle
import sh

from cloudify_cli import utils as cli_utils

from claw import configuration
from claw import tests


class DeployTest(tests.BaseTestWithInit):

    def test_basic(self):
        self._test()

    def test_skip_generation(self):
        self._test(skip_generation=True)

    def test_reset(self):
        self._test(reset=True)

    def test_no_configuration(self):
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.claw.deploy(tests.STUB_CONFIGURATION, tests.STUB_BLUEPRINT)
        self.assertIn('Not initialized', c.exception.stderr)

    def _test(self, skip_generation=False, reset=False):
        self.claw.generate(tests.STUB_CONFIGURATION)
        conf = configuration.Configuration(tests.STUB_CONFIGURATION)
        requests_path = self.workdir / 'requests.json'
        requests_path.write_text('[]')

        def response(body=None, request=None):
            requests = json.loads(requests_path.text())
            requests.append(request)
            requests_path.write_text(json.dumps(requests))
            return bottle.HTTPResponse(
                body=body or {},
                status=201,
                headers={'content-type': 'application/json'})

        def upload_blueprint(blueprint_id):
            return response(request={'blueprint': [blueprint_id]})

        def create_deployment(deployment_id):
            return response(
                request={'deployment': [deployment_id, bottle.request.json]})

        def start_execution():
            return response({'status': 'terminated'},
                            request={'execution': [bottle.request.json]})

        port = self.server({
            ('blueprints/<blueprint_id>', 'PUT'): upload_blueprint,
            ('deployments/<deployment_id>', 'PUT'): create_deployment,
            ('executions', 'POST'): start_execution
        })

        with conf.dir:
            sh.cfy.init()
            with cli_utils.update_wd_settings() as wd_settings:
                wd_settings.set_management_server('localhost')
                wd_settings.set_rest_port(port)

        blueprint_conf = conf.blueprint(tests.STUB_BLUEPRINT)

        if skip_generation or reset:
            self.claw('generate-blueprint',
                      tests.STUB_CONFIGURATION,
                      tests.STUB_BLUEPRINT)

        if skip_generation:
            with blueprint_conf.patch.inputs as patch:
                first_key = patch.obj.keys()[0]
                patch.obj[first_key] = 'SOME_OTHER_VALUE'

        # sanity
        if reset:
            with self.assertRaises(sh.ErrorReturnCode) as c:
                self.claw.deploy(tests.STUB_CONFIGURATION,
                                 tests.STUB_BLUEPRINT)
            self.assertIn('Already initialized', c.exception.stderr)

        self.claw.deploy(tests.STUB_CONFIGURATION, tests.STUB_BLUEPRINT,
                         skip_generation=skip_generation,
                         reset=reset)

        requests = json.loads(requests_path.text())
        blueprint, deployment, execution = requests
        self.assertEqual(blueprint, {
            'blueprint': [tests.STUB_BLUEPRINT]})
        self.assertEqual(deployment, {
            'deployment': [tests.STUB_BLUEPRINT, {
                'blueprint_id': tests.STUB_BLUEPRINT,
                'inputs': blueprint_conf.inputs}]})
        self.assertEqual(execution, {
            'execution': [{
                'deployment_id': tests.STUB_BLUEPRINT,
                'parameters': None,
                'allow_custom_parameters': 'false',
                'workflow_id': 'install',
                'force': 'false'
            }]})
