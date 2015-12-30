#! /usr/bin/env claw
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

"""
See TODO for more details
"""

import argh

from claw import cosmo


@argh.arg('-a', '--almighty-level', help='How almighty is this script?')
def script(world='world', almighty_level=11):
    cosmo.logger.info('Hello {0} from {1}. Almighty level: {2}'.format(
        world,
        cosmo.handler_configuration,
        almighty_level))
