import os

import yaml

import cloudify_rest_client

from systest_manager.settings import Settings

settings = Settings()


class Configuration(object):

    def __init__(self, configuration):
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
        return self._load(self.inputs_path)

    @inputs.setter
    def inputs(self, value):
        self._dump(value, self.inputs_path)

    @property
    def manager_blueprint_dir(self):
        return self.dir / 'manager-blueprint'

    @property
    def manager_blueprint_path(self):
        return self.manager_blueprint_dir / 'manager-blueprint.yaml'

    @property
    def manager_blueprint(self):
        return self._load(self.manager_blueprint_path)

    @manager_blueprint.setter
    def manager_blueprint(self, value):
        self._dump(value, self.manager_blueprint_path)

    @property
    def handler_configuration_path(self):
        return self.dir / 'handler-configuration.yaml'

    @property
    def handler_configuration(self):
        return self._load(self.handler_configuration_path)

    @handler_configuration.setter
    def handler_configuration(self, value):
        self._dump(value, self.handler_configuration_path)

    @property
    def client(self):
        return cloudify_rest_client.CloudifyClient(
            self.handler_configuration['manager_ip'])

    @property
    def tmuxp_path(self):
        return self.dir / 'tmuxp.yaml'

    @staticmethod
    def _load(obj_path):
        return yaml.load(obj_path.text())

    @staticmethod
    def _dump(obj, obj_path):
        obj_path.write_text(yaml.safe_dump(obj, default_flow_style=False))
