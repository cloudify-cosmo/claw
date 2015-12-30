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

import uuid

import sh

from claw import patcher
from claw import commands
from claw import tests


class TestCompletion(tests.BaseTest):

    def setUp(self):
        super(TestCompletion, self).setUp()
        self.scripts_dir = self.workdir / 'scripts'
        self.scripts_dir2 = self.workdir / 'scripts2'
        self.scripts = []
        for scripts_dir in [self.scripts_dir, self.scripts_dir2]:
            scripts_dir.mkdir_p()
            for _ in range(3):
                (scripts_dir / 'script{0}.py'.format(uuid.uuid4())).touch()
            self.scripts += [f.basename() for f in scripts_dir.files()]
        self.init()
        with patcher.YamlPatcher(self.settings.settings_path) as patch:
            patch.obj['scripts'] = [str(self.scripts_dir),
                                    str(self.scripts_dir2)]
        with patcher.YamlPatcher(self.settings.user_suites_yaml) as patch:
            obj = patch.obj
            stub = obj['handler_configurations'][tests.STUB_CONFIGURATION]
            configs = {'conf{0}'.format(i): stub for i in range(3)}
            obj['handler_configurations'] = configs
            self.configurations = configs.keys()
        self.inputs_templates = obj['inputs_override_templates'].keys()
        self.manager_blueprint_templates = obj[
            'manager_blueprint_override_templates'].keys()
        with patcher.YamlPatcher(self.settings.blueprints_yaml) as patch:
            obj = patch.obj
            stub = obj['blueprints'][tests.STUB_BLUEPRINT]
            blueprints = {'blue{0}'.format(i): stub for i in range(3)}
            obj['blueprints'] = blueprints
            self.blueprints = blueprints.keys()
        self.help_args = ['-h', '--help']
        self.existing_configurations = None

    def test_claw(self):
        expected = [f.__name__.replace('_', '-')
                    for f in commands.app.commands]
        expected += self.help_args
        self.assert_completion(expected=expected)

    def test_init(self):
        expected = self.help_args + ['-s', '--suites-yaml',
                                     '-b', '--basedir',
                                     '-r', '--reset']
        self.assert_completion(expected=expected,
                               args=['init'])

    def test_generate(self):
        self._test_generate_and_bootstrap('generate')

    def test_bootstrap(self):
        self._test_generate_and_bootstrap('bootstrap')

    def _test_generate_and_bootstrap(self, command):
        expected = self.configurations + [
            '-i', '--inputs-override',
            '-b', '--manager-blueprint-override',
            '-r', '--reset-config']
        expected += self.help_args
        self.assert_completion(expected=expected,
                               args=[command])

        expected = self.inputs_templates
        for arg in ['-i', '--inputs-override']:
            self.assert_completion(expected=expected,
                                   args=[command, arg])

        expected = self.manager_blueprint_templates
        for arg in ['-b', '--manager-blueprint-override']:
            self.assert_completion(expected=expected,
                                   args=[command, arg])

    def test_status(self):
        self._test_status_and_teardown('status')

    def test_teardown(self):
        self._test_status_and_teardown('teardown')

    def _test_status_and_teardown(self, command):
        self._prepare_existing_configurations()
        expected = self.existing_configurations + self.help_args
        self.assert_completion(expected=expected,
                               args=[command])

    def test_generate_blueprint(self):
        options = self.help_args + ['-r', '--reset']
        self._test_generate_blueprint_and_deploy_and_undeploy(
            'generate-blueprint', options)

    def test_deploy(self):
        options = self.help_args + ['-r', '--reset',
                                    '-s', '--skip-generation',
                                    '-t', '--timeout']
        self._test_generate_blueprint_and_deploy_and_undeploy('deploy',
                                                              options)

    def test_undeploy(self):
        options = self.help_args + ['--cancel-executions']
        self._test_generate_blueprint_and_deploy_and_undeploy('undeploy',
                                                              options)

    def _test_generate_blueprint_and_deploy_and_undeploy(self, command,
                                                         options):
        self._prepare_existing_configurations()
        expected = self.existing_configurations + options
        self.assert_completion(expected=expected,
                               args=[command])
        expected = self.blueprints + options
        self.assert_completion(expected=expected,
                               args=[command,
                                     self.configurations[0]])

    def test_cleanup_deployments(self):
        self._prepare_existing_configurations()
        options = self.help_args + ['--cancel-executions']
        expected = self.existing_configurations + options
        self.assert_completion(expected=expected,
                               args=['cleanup-deployments'])

    def test_cleanup(self):
        expected = self.configurations + self.help_args
        self.assert_completion(expected=expected,
                               args=['cleanup'])

    def test_overview(self):
        self._prepare_existing_configurations()
        expected = self.existing_configurations + self.help_args
        expected += ['-p', '--port']
        self.assert_completion(expected=expected,
                               args=['overview'])

    def test_events(self):
        self._prepare_existing_configurations()
        options = self.help_args + ['-o', '--output',
                                    '-b', '--batch-size',
                                    '-i', '--include-logs',
                                    '-t', '--timeout']
        expected = self.existing_configurations + options
        self.assert_completion(expected=expected,
                               args=['events'])

    def test_script(self):
        self._prepare_existing_configurations()
        expected = self.existing_configurations + self.help_args
        self.assert_completion(expected=expected,
                               args=['script'])
        expected = self.scripts + self.help_args
        self.assert_completion(expected=expected,
                               args=['script',
                                     self.existing_configurations[0]])

    def test_generate_script(self):
        expected = ['-r', '--rewrite'] + self.help_args
        self.assert_completion(expected=expected,
                               args=['generate-script'],
                               filter_non_options=True)

    def _prepare_existing_configurations(self):
        self.existing_configurations = list(self.configurations)[:2]
        for conf in self.existing_configurations:
            self.claw.generate(conf)

    def assert_completion(self, expected, args=None,
                          filter_non_options=False):
        args = args or []
        args += ["''"]
        cmd = ['claw'] + list(args)
        partial_word = cmd[-1]
        cmdline = ' '.join(cmd)
        lines = [
            'set -e',
            'eval "$(register-python-argcomplete claw)"',
            'export COMP_LINE="{}"'.format(cmdline),
            'export COMP_WORDS=({})'.format(cmdline),
            'export COMP_CWORD={}'.format(cmd.index(partial_word)),
            'export COMP_POINT={}'.format(len(cmdline)),
            '_python_argcomplete {}'.format(cmd[0]),
            'echo ${COMPREPLY[*]}'
        ]
        script_path = self.workdir / 'completions.sh'
        script_path.write_text('\n'.join(lines))
        p = sh.bash(script_path)
        completions = p.stdout.strip().split(' ')
        if filter_non_options:
            completions = [c for c in completions if c.startswith('-')]
        self.assertEqual(len(expected), len(completions))
        for expected_completion in expected:
            self.assertIn(expected_completion, completions)
