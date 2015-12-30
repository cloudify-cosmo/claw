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
This script was generated as part of `claw init` or explicitly by calling
`claw generate-script`.

There are several ways to run this script:
1) Using `claw script CONFIGURATION_NAME FULL_PATH_TO_SCRIPT` will execute
the script with the configuration CONFIGURATION_NAME as the configuration
represented by the `cosmo` import.
2) If this script is located under $CLAW_HOME/scripts (or any other scripts
dir that is explicitly added to ~/.claw) It can be executed less verbosely by
specifying the filename only without the full path, for example if there is a
script named my_script.py under $CLAW_HOME/scripts, it can be executed by
running: `claw script CONFIGURATION_NAME my_script.py`
3) Notice the `#! /usr/bin/env claw` line at the beginning of this script.
This tells us the `claw` is capable of executing this script if passed as it's
first argument. If called directly, the active configuration represented by
the `cosmo` import, will be the configuration that was `claw generate`-ed or
`claw bootstrap`-ed most recently.

The `cosmo` import below serves as your entry point to the cosmo, which
represents a configuration.
Some useful things that the cosmo holds:
- `cosmo.client` will returned an Cloudify REST client already configured.
- `cosmo.ssh` will configure a fabric env to connect to the Cloudify manager.
usage example:
```
with cosmo.ssh() as ssh:
    ssh.run('echo $HOME')
```
- `cosmo.inputs` will return the inputs used for bootstrapping.
- `cosmo.handler_configuration` is the generated handler_configuration used
when running system tests locally.
- To see other things exposed by `cosmo` take a look at the
`claw.configuration:Configuration` class code.

When a script is executed, if no function name is supplied as an additional
argument, a function named `script` is searched for, and executed if found.
If a function name is supplied, e.g. `claw script CONF SCRIPT_PATH func_name`,
it will be executed instead.

Functions are executed by leveraging the `argh` library. This library makes it
easy to pass additional configuration to the function with very little effort
in terms of argument parsing. You can read more about argh in
http://argh.readthedocs.org
"""

import argh

from claw import cosmo


# Adding the arg decorator is not required but can be used to provided
# help strings and similar. Most of these arguments are deleted by argh
# to parser.add_argument, some are specific to argh
@argh.arg('-a', '--almighty-level', help='How almighty is this script?')
def script(world='world', almighty_level=11):
    cosmo.logger.info('Hello {0} from {1}. Almighty level: {2}'.format(
        world,
        cosmo.handler_configuration,
        almighty_level))
