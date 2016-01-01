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


class GenerateScriptTest(tests.BaseTestWithInit):

    def setUp(self):
        super(GenerateScriptTest, self).setUp()
        self.claw.generate(tests.STUB_CONFIGURATION)

    def test_basic(self, reset=False):
        script_path = self.workdir / 'script.sh'
        self.claw('generate-script', script_path, reset=reset)
        script = sh.Command(script_path)
        self.assertIn("'handler': 'openstack_handler'",
                      script().stdout.strip())
        return script_path

    def test_exists_no_rewrite(self):
        script_path = self.test_basic()
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.test_basic()
        self.assertIn('{0} already exists'.format(script_path),
                      c.exception.stderr)

    def test_exists_with_rewrite(self):
        self.test_basic()
        self.test_basic(reset=True)
