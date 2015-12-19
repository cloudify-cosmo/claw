import os

from path import path

from systest_manager import settings
from systest_manager import configuration
from systest_manager import tests


class TestConfiguration(tests.BaseTest):

    def test_init_from_dir(self):
        conf = configuration.Configuration(self.workdir)
        self.assertEqual(conf.configuration,
                         self.workdir.basename())

    def test_init_from_current_dir(self):
        conf = configuration.Configuration()
        self.assertEqual(conf.configuration,
                         path(os.getcwd()).basename())

    def test_init_from_current_configuration(self):
        self.init()
        conf = configuration.Configuration(configuration.CURRENT_CONFIGURATION)
        self.assertEqual(conf.configuration,
                         configuration.CURRENT_CONFIGURATION)
        self.systest.generate(tests.STUB_CONFIGURATION)
        conf = configuration.Configuration(configuration.CURRENT_CONFIGURATION)
        self.assertEqual(conf.configuration, tests.STUB_CONFIGURATION)

    def test_exists(self):
        self.init()
        conf = configuration.Configuration(tests.STUB_CONFIGURATION)
        self.assertFalse(conf.exists())
        self.systest.generate(tests.STUB_CONFIGURATION)
        conf = configuration.Configuration(configuration.CURRENT_CONFIGURATION)
        self.assertTrue(conf.exists())

    def test_configuration_properties(self):
        self.init()
        self.systest.generate(tests.STUB_CONFIGURATION)
        conf = configuration.Configuration(tests.STUB_CONFIGURATION)
        conf_dir = self.workdir / 'configurations' / tests.STUB_CONFIGURATION
        self.assertEqual(conf.dir, conf_dir)
        self.assertEqual(conf.manager_blueprint_dir,
                         conf_dir / 'manager-blueprint')
        self.assertEqual(conf.blueprints_dir,
                         conf_dir / 'blueprints')
        self.assertEqual(conf.inputs_path,
                         conf_dir / 'inputs.yaml')
        self.assertEqual(
            conf.manager_blueprint_path,
            conf_dir / 'manager-blueprint' / 'manager-blueprint.yaml')
        self.assertEqual(conf.handler_configuration_path,
                         conf_dir / 'handler-configuration.yaml')
        self.assertEqual(conf.cli_config_path,
                         conf_dir / '.cloudify' / 'config.yaml')
        self.assertEqual(conf.properties, {})
