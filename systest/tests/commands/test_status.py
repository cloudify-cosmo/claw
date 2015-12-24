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

from systest import configuration
from systest import tests


class StatusTest(tests.BaseTest):

    def setUp(self):
        super(StatusTest, self).setUp()
        self.init()

    def test_basic(self):
        # TODO
        pass

    def test_no_configuration(self):
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.systest.status(tests.STUB_CONFIGURATION)
        self.assertIn('Not initialized', c.exception.stderr)

    def test_no_manager_ip(self):
        self.systest.generate(tests.STUB_CONFIGURATION)
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.systest.status(tests.STUB_CONFIGURATION)
        self.assertIn('Not bootstrapped', c.exception.stderr)

    def test_no_connectivity_to_manager(self):
        self.systest.generate(tests.STUB_CONFIGURATION)
        conf = configuration.Configuration(tests.STUB_CONFIGURATION)
        ip = '127.0.0.1'
        with conf.patch.handler_configuration as patch:
            patch.set_value('manager_ip', ip)
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.systest.status(tests.STUB_CONFIGURATION)
        self.assertIn('Not reachable', c.exception.stderr)
        self.assertIn(ip, c.exception.stderr)