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
from systest.tests.commands.test_bootstrap import BaseBootstrapTest


class TeardownTest(BaseBootstrapTest):

    def test_basic(self):
        configuration_name = self._test()
        conf = configuration.Configuration(configuration_name)
        self.systest.teardown(configuration_name)
        self.assertEqual('delete invoked',
                         (conf.dir / 'delete.output').text())

    def test_no_configuration(self):
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.systest.teardown(tests.STUB_CONFIGURATION)
        self.assertIn('Not initialized', c.exception.stderr)
