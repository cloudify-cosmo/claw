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

import os
import shutil
import tempfile
import unittest
import multiprocessing

import bottle
import sh
from path import path

import cosmo_tester
from cloudify_rest_client.client import DEFAULT_API_VERSION
from cloudify.proxy.server import get_unused_port

from claw import settings
from claw import configuration


STUB_CONFIGURATION = 'sample_openstack_env'
STUB_BLUEPRINT = 'openstack_nodecellar'


class BaseTest(unittest.TestCase):

    def setUp(self):
        self.workdir = path(tempfile.mkdtemp(prefix='claw-tests-'))
        self.settings_path = self.workdir / 'settings'
        self.settings = settings.Settings()
        os.environ[settings.CLAW_SETTINGS] = str(self.settings_path)
        self.addCleanup(self.cleanup)
        system_tests_dir = path(cosmo_tester.__file__).dirname().dirname()
        self.main_suites_yaml_path = (system_tests_dir / 'suites' / 'suites' /
                                      'suites.yaml')
        self.claw = sh.claw

    def cleanup(self):
        configuration.settings = settings.Settings()
        shutil.rmtree(self.workdir, ignore_errors=True)
        os.environ.pop(settings.CLAW_SETTINGS, None)

    def init(self, suites_yaml=None):
        options = {}
        if suites_yaml:
            options['suites_yaml'] = suites_yaml
        with self.workdir:
            self.claw.init(**options)

    def server(self, routes):
        port = get_unused_port()
        app = bottle.app()
        for route, handler in routes.items():
            method = 'GET'
            if isinstance(route, tuple):
                route, method = route
            route = '/api/{0}/{1}'.format(DEFAULT_API_VERSION, route)
            app.route(route, method=method)(handler)
        p = multiprocessing.Process(target=lambda: app.run(port=port,
                                                           quiet=True))
        p.start()
        self.addCleanup(lambda: (p.terminate(), p.join()))
        return port


class BaseTestWithInit(BaseTest):

    def setUp(self):
        super(BaseTestWithInit, self).setUp()
        self.init()
