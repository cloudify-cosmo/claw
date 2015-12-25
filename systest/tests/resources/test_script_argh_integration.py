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


def script(arg1, arg2, str_kwarg='str', boolean_flag=False,
           int_kwarg=3):
    print json.dumps({
        'args': [arg1, arg2],
        'kwargs': {
            'str_kwarg': str_kwarg,
            'int_kwarg': int_kwarg,
            'boolean_flag': boolean_flag
        }
    })
