import sys
import os
import logging
import importlib
from contextlib import contextmanager

import fabric
import fabric.context_managers
import fabric.api
import yaml

import cloudify_rest_client
from cosmo_tester.framework import util

from systest_manager import patcher
from systest_manager.settings import Settings

CURRENT_CONFIGURATION = '+'

settings = Settings()


class Configuration(object):

    def __init__(self, configuration='.'):
        if os.path.isdir(configuration):
            configuration = os.path.basename(os.path.abspath(configuration))
        self.configuration = configuration
        if configuration == CURRENT_CONFIGURATION and self.exists():
            self.configuration = os.path.basename(os.path.realpath(self.dir))
        self._logger = None

    def exists(self):
        return self.inputs_path.exists()

    @property
    def dir(self):
        return settings.configurations / self.configuration

    @property
    def manager_blueprint_dir(self):
        return self.dir / 'manager-blueprint'

    @property
    def blueprints_dir(self):
        return self.dir / 'blueprints'

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
    def manager_blueprint_path(self):
        return self.manager_blueprint_dir / 'manager-blueprint.yaml'

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
    def properties(self):
        handler_configuration = self.handler_configuration
        properties_name = handler_configuration.get('properties')
        if not properties_name:
            return {}
        suites_yaml = self.load(settings.main_suites_yaml)
        handler_properties = suites_yaml.get('handler_properties', {})
        properties = handler_properties.get(properties_name, {})
        return util.process_variables(suites_yaml, properties)

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

    @property
    def patch(self):
        return patcher.ConfigurationPatcher(self)

    @contextmanager
    def ssh(self):
        with fabric.context_managers.settings(
                host_string=self.handler_configuration.get('manager_ip'),
                user=self.handler_configuration.get('manager_user'),
                key_filename=self.handler_configuration.get('manager_key')):
            yield fabric.api

    @property
    def logger(self):
        if not self._logger:
            logger = logging.getLogger(self.configuration)
            logger.handlers = []
            handler = logging.StreamHandler(sys.stdout)
            fmt = '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
            handler.setFormatter(logging.Formatter(fmt))
            handler.setLevel(logging.DEBUG)
            logger.setLevel(logging.DEBUG)
            logger.addHandler(handler)
            self._logger = logger
        return self._logger

    def blueprint(self, blueprint):
        return Blueprint(blueprint, self)

    @staticmethod
    def load(obj_path):
        return yaml.load(obj_path.text()) or {}

    @staticmethod
    def dump(obj, obj_path):
        obj_path.write_text(yaml.safe_dump(obj, default_flow_style=False))


class Blueprint(object):

    def __init__(self, blueprint, configuration):
        self.blueprint_name = blueprint
        self.configuration = configuration

    @property
    def dir(self):
        return self.configuration.blueprints_dir / self.blueprint_name

    @property
    def blueprint_configuration_path(self):
        return self.dir / 'blueprint-configuration.yaml'

    @property
    def blueprint_configuration(self):
        return self.configuration.load(self.blueprint_configuration_path)

    @blueprint_configuration.setter
    def blueprint_configuration(self, value):
        self.configuration.dump(value, self.blueprint_configuration_path)

    @property
    def inputs_path(self):
        return self.dir / 'inputs.yaml'

    @property
    def inputs(self):
        return self.configuration.load(self.inputs_path)

    @inputs.setter
    def inputs(self, value):
        self.configuration.dump(value, self.inputs_path)

    @property
    def blueprint_path(self):
        return self.dir / 'blueprint' / 'blueprint.yaml'

    @property
    def blueprint(self):
        return self.configuration.load(self.blueprint_path)

    @blueprint.setter
    def blueprint(self, value):
        self.configuration.dump(value, self.blueprint_path)

    @property
    def patch(self):
        return patcher.ConfigurationPatcher(self)
