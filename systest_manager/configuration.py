import importlib

import yaml

from settings import Settings

settings = Settings()


class Configuration(object):

    def __init__(self, configuration):
        self.configuration = configuration

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
    def handler(self):
        handler_module_path = 'system_tests.{0}'.format(
            self.handler_configuration['handler'])
        handler_module = importlib.import_module(handler_module_path)
        handler_cls = handler_module.handler
        return handler_cls

    def _load(self, obj_path):
        return yaml.load(obj_path.text())

    def _dump(self, obj, obj_path):
        obj_path.write_text(yaml.safe_dump(obj, default_flow_style=False))
