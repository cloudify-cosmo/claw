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


class EntryPointTests(tests.BaseTest):

    configuration = tests.STUB_CONFIGURATION

    def test_command_error(self):
        self.init()
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.claw.script('I DONT EXIST', 'STUB_PATH')
        self.assertIn('error: Not initialized', c.exception.stderr)

    def test_direct_script_execution(self):
        text = 'TEXT'
        script = '''
from claw import cosmo
def script(arg):
    print arg + ':' + cosmo.configuration
'''
        p = self._run_script(script, text)
        self.assertEqual('{0}:{1}'.format(text, self.configuration),
                         p.stdout.strip())

    def test_direct_script_execution_error(self):
        script = '''
def script(arg):
    raise RuntimeError(arg)
'''
        message = 'MESSAGE'
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self._run_script(script, message)
        self.assertIn('RuntimeError: {0}'.format(message), c.exception.stderr)

    def test_direct_script_execution_command_error(self):
        self.init()
        script_path = self.workdir / 'script.py'
        script_path.touch()
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.claw(script_path)
        self.assertIn('error: Not initialized', c.exception.stderr)

    def _run_script(self, script, *args):
        self.init()
        self.claw.generate(self.configuration)
        script_path = self.workdir / 'script.py'
        script_path.write_text(script)
        return self.claw(script_path, *args)
