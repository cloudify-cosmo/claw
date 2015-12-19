import logging
import os

import yaml
import fabric.api
from path import path

from systest_manager import settings
from systest_manager import configuration
from systest_manager import tests
from systest_manager.handlers import stub_handler


class TestConfiguration(tests.BaseTest):

    def cleanup(self):
        configuration.settings = settings.Settings()
        super(TestConfiguration, self).cleanup()

    def test_init_from_dir(self):
        conf = configuration.Configuration(self.workdir)
        self.assertEqual(conf.configuration, self.workdir.basename())

    def test_init_from_current_dir(self):
        conf = configuration.Configuration()
        self.assertEqual(conf.configuration, path(os.getcwd()).basename())

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
        conf = configuration.Configuration(tests.STUB_CONFIGURATION)
        self.assertTrue(conf.exists())

    def test_configuration_properties(self):
        conf, blueprint = self._init_configuration_and_blueprint()

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

        blueprint_dir = conf.blueprints_dir / tests.STUB_BLUEPRINT
        self.assertIs(blueprint.configuration, conf)
        self.assertEqual(blueprint.blueprint_name, tests.STUB_BLUEPRINT)
        self.assertEqual(blueprint.dir, blueprint_dir)
        self.assertEqual(blueprint.blueprint_configuration_path,
                         blueprint_dir / 'blueprint-configuration.yaml')
        self.assertEqual(blueprint.inputs_path,
                         blueprint_dir / 'inputs.yaml')
        self.assertEqual(blueprint.blueprint_path,
                         blueprint_dir / 'blueprint' / 'blueprint.yaml')

    def test_yaml_files(self):
        conf, blueprint = self._init_configuration_and_blueprint()
        conf_dir = self.workdir / 'configurations' / tests.STUB_CONFIGURATION
        blueprint_dir = conf.blueprints_dir / tests.STUB_BLUEPRINT
        conf.cli_config_path.dirname().mkdir_p()

        configuration_files = [
            ('inputs', conf_dir / 'inputs.yaml'),
            ('handler_configuration', conf_dir / 'handler-configuration.yaml'),
            ('manager_blueprint',
             conf_dir / 'manager-blueprint' / 'manager-blueprint.yaml'),
            ('cli_config', conf_dir / '.cloudify' / 'config.yaml'),
        ]
        blueprint_files = [
            ('inputs', blueprint_dir / 'inputs.yaml'),
            ('blueprint', blueprint_dir / 'blueprint' / 'blueprint.yaml'),
            ('blueprint_configuration',
             blueprint_dir / 'blueprint-configuration.yaml')
        ]

        def assert_files(obj, files):
            content = {'some': 'value'}
            for _file in files:
                setattr(obj, _file[0], content)
            if isinstance(obj, configuration.Configuration):
                new_obj = configuration.Configuration(tests.STUB_CONFIGURATION)
            else:
                new_obj = conf.blueprint(tests.STUB_BLUEPRINT)
            for _file in files:
                self.assertEqual(content, getattr(new_obj, _file[0]))
                self.assertEqual(yaml.safe_load(_file[1].text()), content)
        assert_files(conf, configuration_files)
        assert_files(blueprint, blueprint_files)

    def test_properties(self):
        props_name = 'props1'
        main_suites_yaml_path = self.workdir / 'main-suites.yaml'
        main_suites_yaml = {
            'variables': {'a': '123'},
            'handler_properties': {
                props_name: {
                    'a_from_var': '{{a}}',
                    'b': 'b_val'
                }
            }
        }
        main_suites_yaml_path.write_text(yaml.safe_dump(main_suites_yaml))
        conf = self._init_configuration(main_suites_yaml_path)
        with conf.patch.handler_configuration as patch:
            patch.obj.pop('properties', None)
        self.assertEqual(conf.properties, {})
        with conf.patch.handler_configuration as patch:
            patch.obj['properties'] = 'no_such_properties'
        self.assertEqual(conf.properties, {})
        with conf.patch.handler_configuration as patch:
            patch.obj['properties'] = props_name
        self.assertEqual(conf.properties, {
            'a_from_var': '123',
            'b': 'b_val'
        })

    def test_client(self):
        conf = self._init_configuration()
        self.assertEqual(conf.client._client.host, 'localhost')
        ip = '1.1.1.1'
        with conf.patch.handler_configuration as patch:
            patch.obj['manager_ip'] = ip
        self.assertEqual(conf.client._client.host, ip)

    def test_systest_handler(self):
        conf = self._init_configuration()
        with conf.patch.handler_configuration as patch:
            patch.set_value('handler', 'stub_handler')
        systest_handler = conf.systest_handler
        self.assertTrue(isinstance(systest_handler, stub_handler.Handler))
        self.assertIs(systest_handler.configuration, conf)

    def test_patch(self):
        conf, blueprint = self._init_configuration_and_blueprint()
        key = 'some_key'
        value = 'some_value'
        conf.cli_config_path.dirname().makedirs_p()
        conf.cli_config_path.write_text('{}')

        def _assert_patching(obj, props):
            for prop in props:
                with getattr(obj.patch, prop) as patch:
                    patch.set_value(key, value)
                self.assertEqual(getattr(obj, prop)[key], value)
        _assert_patching(conf, ['inputs',
                                'manager_blueprint',
                                'handler_configuration',
                                'cli_config'])
        _assert_patching(blueprint, ['inputs',
                                     'blueprint',
                                     'blueprint_configuration'])

    def test_ssh(self):
        conf = self._init_configuration()
        ip = '1.1.1.1'
        user = 'user'
        key = '~/key'
        with conf.patch.handler_configuration as patch:
            patch.obj.update({
                'manager_ip': ip,
                'manager_user': user,
                'manager_key': key
            })
        with conf.ssh() as ssh:
            self.assertEqual(ssh, fabric.api)
            self.assertEqual(fabric.api.env['host_string'], ip)
            self.assertEqual(fabric.api.env['user'], user)
            self.assertEqual(fabric.api.env['key_filename'], key)

    def test_logger(self):
        conf = self._init_configuration()
        logger = conf.logger
        self.assertTrue(isinstance(logger, logging.Logger))
        self.assertEqual(1, len(logger.handlers))

    def _init_configuration(self, suites_yaml=None):
        self.init(suites_yaml)
        self.systest.generate(tests.STUB_CONFIGURATION)
        return configuration.Configuration(tests.STUB_CONFIGURATION)

    def _init_configuration_and_blueprint(self):
        import sh
        conf = self._init_configuration()
        try:
            self.systest('generate-blueprint',
                         tests.STUB_CONFIGURATION,
                         tests.STUB_BLUEPRINT)
        except sh.ErrorReturnCode as e:
            raise RuntimeError(e.stderr)
        blueprint = conf.blueprint(tests.STUB_BLUEPRINT)
        return conf, blueprint
