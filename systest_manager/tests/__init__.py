import os
import shutil
import tempfile
import unittest

import sh
from path import path

import cosmo_tester

from systest_manager import settings


systest = sh.systest


STUB_CONFIGURATION = 'some_openstack_env'


class BaseTest(unittest.TestCase):

    def setUp(self):
        self.workdir = path(tempfile.mkdtemp(prefix='systest-tests-'))
        os.environ[settings.SYSTEST_SETTINGS] = str(self.workdir / 'settings')
        self.addCleanup(self.cleanup)

        system_tests_dir = path(cosmo_tester.__file__).dirname().dirname()
        self.main_suites_yaml_path = (system_tests_dir / 'suites' / 'suites' /
                                      'suites.yaml')

        self.systest = systest

    def cleanup(self):
        shutil.rmtree(self.workdir, ignore_errors=True)
        del os.environ[settings.SYSTEST_SETTINGS]

    def init(self):
        with self.workdir:
            self.systest.init(suites_yaml=self.main_suites_yaml_path)
