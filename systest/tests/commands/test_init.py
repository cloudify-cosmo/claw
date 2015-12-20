import sh
from path import path

import cosmo_tester

from systest import resources
from systest import settings
from systest import tests


class InitTest(tests.BaseTest):

    def setUp(self):
        super(InitTest, self).setUp()
        self.settings = settings.Settings()

    def test_basic(self, reset=False):
        with self.workdir:
            self.systest.init(suites_yaml=self.main_suites_yaml_path,
                              reset=reset)
        self._verify_init(expected_basedir=self.workdir,
                          expected_suites_yaml=self.main_suites_yaml_path)

    def test_settings_exists_no_reset(self):
        self.test_basic()
        with self.assertRaises(sh.ErrorReturnCode):
            self.test_basic()

    def test_settings_exists_reset(self):
        self.test_basic()
        self.test_basic(reset=True)

    def test_suites_yaml_points_to_system_tests_dir(self):
        suites_yaml = path(cosmo_tester.__file__).dirname().dirname()
        with self.workdir:
            self.systest.init(suites_yaml=suites_yaml)
        self._verify_init(expected_basedir=self.workdir,
                          expected_suites_yaml=self.main_suites_yaml_path)

    def test_missing_suites_yaml_argument(self):
        with self.assertRaises(sh.ErrorReturnCode):
            self.systest.init()

    def test_suites_yaml_does_not_exist(self):
        # sanity
        with self.workdir:
            self.systest.init(suites_yaml=self.main_suites_yaml_path)
            with self.assertRaises(sh.ErrorReturnCode):
                self.systest.init(
                    suites_yaml='some_path_that_does_not_exist.yaml')

    def test_explicit_basedir(self):
        basedir = self.workdir / 'basedir'
        basedir.mkdir()
        with self.workdir:
            self.systest.init(suites_yaml=self.main_suites_yaml_path,
                              basedir=basedir)
        self._verify_init(expected_basedir=basedir,
                          expected_suites_yaml=self.main_suites_yaml_path)

    def _verify_init(self,
                     expected_basedir,
                     expected_suites_yaml):
        self.assertTrue(self.settings.settings_path.exists())
        self.assertEqual(self.settings.basedir, expected_basedir)
        self.assertEqual(self.settings.main_suites_yaml, expected_suites_yaml)
        self.assertEqual(self.settings.user_suites_yaml.text(),
                         resources.get('templates/suites.template.yaml'))
        self.assertEqual(self.settings.blueprints_yaml.text(),
                         resources.get('templates/blueprints.template.yaml'))
        self.assertTrue(self.settings.configurations.exists())
