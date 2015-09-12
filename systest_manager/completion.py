class Completion(object):

    def __init__(self, settings):
        self._settings = settings

    def _configurations(self):
        return self._settings.load_suites_yaml(variables=False)[
            'handler_configurations'].keys()

    def _blueprints(self):
        return self._settings.load_blueprints_yaml(variables=False)[
            'blueprints'].keys()

    def all_blueprints(self, prefix, **kwargs):
        return (b for b in self._blueprints()
                if b.startswith(prefix))

    def all_configurations(self, prefix, **kwargs):
        return (c for c in self._configurations()
                if c.startswith(prefix))

    def existing_configurations(self, prefix, **kwargs):
        return (c for c in self.all_configurations(prefix)
                if (self._settings.basedir / c).exists())

    def script_paths(self, prefix, **kwargs):
        for script_dir in self._settings.scripts:
            for script_path in script_dir.files():
                basename = script_path.basename()
                if basename.startswith(prefix):
                    yield basename
