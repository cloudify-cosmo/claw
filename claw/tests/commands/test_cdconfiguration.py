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

from claw import tests


class CDConfigurationTest(tests.BaseTest):

    def test_cdconfiguration(self):
        self.init()
        self.claw.generate(tests.STUB_CONFIGURATION)
        script = [
            'eval "$(claw cdconfiguration)"',
            'cdconfiguration {0}'.format(tests.STUB_CONFIGURATION),
            'echo $PWD'
        ]
        script_path = self.workdir / 'script.sh'
        script_path.write_text('\n'.join(script))
        self.assertEqual(
            self.settings.configurations / tests.STUB_CONFIGURATION,
            sh.bash(script_path).stdout.strip())

    def test_cdconfiguration_no_init(self):
        self.assertEqual('', self.claw.cdconfiguration().stdout)

    def test_cdconfiguration_bash_completion(self):
        self.init()
        self.claw.generate(tests.STUB_CONFIGURATION)
        cmd = ['cdconfiguration', "''"]
        partial_word = cmd[-1]
        cmdline = ' '.join(cmd)
        lines = [
            'eval "$(claw cdconfiguration)"',
            'export COMP_LINE="{}"'.format(cmdline),
            'export COMP_WORDS=({})'.format(cmdline),
            'export COMP_CWORD={}'.format(cmd.index(partial_word)),
            'export COMP_POINT={}'.format(len(cmdline)),
            '__claw_cdconfiguration_completion'.format(cmd[0]),
            'echo ${COMPREPLY[*]}'
        ]
        script_path = self.workdir / 'completions.sh'
        script_path.write_text('\n'.join(lines))
        self.assertEqual(
            set([tests.STUB_CONFIGURATION, '+']),
            set(sh.bash(script_path).stdout.strip().split(' ')))
