class Completion(object):

    def __init__(self, settings):
        self._settings = settings

    def _configurations(self):
        return self._settings.load_suites_yaml(variables=False)[
            'handler_configurations'].keys()

    def _blueprints(self):
        return self._settings.load_blueprints_yaml(variables=False)[
            'blueprints'].keys()

    def _input_override_templates(self):
        return self._settings.load_suites_yaml(variables=False)[
            'inputs_override_templates']

    def _manager_blueprint_override_templates(self):
        return self._settings.load_suites_yaml(variables=False)[
            'manager_blueprint_override_templates']

    def all_blueprints(self, prefix, **kwargs):
        return (b for b in self._blueprints()
                if b.startswith(prefix))

    def all_configurations(self, prefix, **kwargs):
        return (c for c in self._configurations()
                if c.startswith(prefix))

    def existing_configurations(self, prefix, **kwargs):
        return (c for c in self.all_configurations(prefix)
                if (self._settings.configurations / c).exists())

    def input_override_templates(self, prefix, **kwargs):
        return (io for io in self._input_override_templates()
                if io.startswith(prefix))

    def manager_blueprint_override_templates(self, prefix, **kwargs):
        return (mbo for mbo in self._manager_blueprint_override_templates()
                if mbo.startswith(prefix))

    def script_paths(self, prefix, **kwargs):
        for script_dir in self._settings.scripts:
            for script_path in script_dir.files():
                basename = script_path.basename()
                if basename.startswith(prefix):
                    yield basename
