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

import fabric.api

from cloudify import ctx


def stub(*args, **kwargs):
    pass

fabric.api.put = stub
fabric.api.run = stub

props = ctx.node.properties
ctx.instance.runtime_properties.update({
    'rest_port': props['rest_port'],
    'manager_ip': props['ip'],
    'manager_user': props['ssh_user'],
    'manager_key_path': props['ssh_key_filename'],
    'provider': {'some': 'key'}
})
