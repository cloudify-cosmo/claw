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
from cloudify.proxy.server import get_unused_port

from systest import settings
from systest import configuration


systest = sh.systest


STUB_CONFIGURATION = 'some_openstack_env'
STUB_BLUEPRINT = 'openstack_nodecellar'


class BaseTest(unittest.TestCase):

    def setUp(self):
        self.workdir = path(tempfile.mkdtemp(prefix='systest-tests-'))
        self.settings_path = self.workdir / 'settings'
        os.environ[settings.SYSTEST_SETTINGS] = str(self.settings_path)
        self.addCleanup(self.cleanup)

        system_tests_dir = path(cosmo_tester.__file__).dirname().dirname()
        self.main_suites_yaml_path = (system_tests_dir / 'suites' / 'suites' /
                                      'suites.yaml')

        self.systest = systest

    def cleanup(self):
        configuration.settings = settings.Settings()
        shutil.rmtree(self.workdir, ignore_errors=True)
        os.environ.pop(settings.SYSTEST_SETTINGS, None)

    def init(self, suites_yaml=None):
        options = {}
        if suites_yaml:
            options['suites_yaml'] = suites_yaml
        with self.workdir:
            self.systest.init(**options)

    def server(self, routes):
        port = get_unused_port()
        app = bottle.app()
        for route, handler in routes.items():
            app.route(route)(handler)
        p = multiprocessing.Process(target=lambda: app.run(port=port,
                                                           quiet=True))
        p.start()
        self.addCleanup(lambda: (p.terminate(), p.join()))
        return port


class BaseTestWithInit(BaseTest):

    def setUp(self):
        super(BaseTestWithInit, self).setUp()
        self.init()
