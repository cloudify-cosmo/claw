from systest_manager import configuration as _configuration


class Blueprint(object):

    def __init__(self, blueprint, configuration):
        self.blueprint = blueprint
        self.configuration = configuration

    @property
    def dir(self):
        return self.configuration.blueprints_dir / self.blueprint

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
        self.configuration.dump(value, self.blueprint)

    @property
    def patch(self):
        return _configuration.ConfigurationPatcher(self)
