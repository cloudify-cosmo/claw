import os
import importlib

import yaml

import cloudify_rest_client
from cosmo_tester.framework import util


from systest_manager.settings import Settings

settings = Settings()


class Configuration(object):

    def __init__(self, configuration='.'):
        if os.path.isdir(configuration):
            configuration = os.path.basename(os.path.abspath(configuration))
        self.configuration = configuration

    def exists(self):
        return self.inputs_path.exists()

    @property
    def dir(self):
        return settings.basedir / self.configuration

    @property
    def inputs_path(self):
        return self.dir / 'inputs.yaml'

    @property
    def inputs(self):
        return self.load(self.inputs_path)

    @inputs.setter
    def inputs(self, value):
        self.dump(value, self.inputs_path)

    @property
    def manager_blueprint_dir(self):
        return self.dir / 'manager-blueprint'

    @property
    def manager_blueprint_path(self):
        return self.manager_blueprint_dir / 'manager-blueprint.yaml'

    @property
    def blueprints_dir(self):
        return self.dir / 'blueprints'

    @property
    def manager_blueprint(self):
        return self.load(self.manager_blueprint_path)

    @manager_blueprint.setter
    def manager_blueprint(self, value):
        self.dump(value, self.manager_blueprint_path)

    @property
    def handler_configuration_path(self):
        return self.dir / 'handler-configuration.yaml'

    @property
    def handler_configuration(self):
        return self.load(self.handler_configuration_path)

    @property
    def properties(self):
        handler_configuration = self.handler_configuration
        properties_name = handler_configuration.get('properties')
        if not properties_name:
            return {}
        suites_yaml = self.load(settings.main_suites_yaml)
        handler_properties = suites_yaml.get('handler_properties')
        properties = handler_properties.get(properties_name, {})
        return util.process_variables(suites_yaml, properties)

    @handler_configuration.setter
    def handler_configuration(self, value):
        self.dump(value, self.handler_configuration_path)

    @property
    def cli_config_path(self):
        return self.dir / '.cloudify' / 'config.yaml'

    @property
    def cli_config(self):
        return self.load(self.cli_config_path)

    @cli_config.setter
    def cli_config(self, value):
        self.dump(value, self.cli_config_path)

    @property
    def client(self):
        return cloudify_rest_client.CloudifyClient(
            self.handler_configuration['manager_ip'])

    @property
    def systest_handler(self):
        handler_name = self.handler_configuration['handler']
        module = importlib.import_module(
            'systest_manager.handlers.{0}'.format(handler_name))
        return module.Handler(self)

    @staticmethod
    def load(obj_path):
        return yaml.load(obj_path.text())

    @staticmethod
    def dump(obj, obj_path):
        obj_path.write_text(yaml.safe_dump(obj, default_flow_style=False))
