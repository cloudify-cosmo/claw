class Completion(object):

    def __init__(self, settings):
        self._settings = settings

    def _configurations(self):
        return self._settings.load_suites_yaml(variables=False)[
            'handler_configurations'].keys()

    def all_configurations(self, prefix, **kwargs):
        return (c for c in self._configurations()
                if c.startswith(prefix))

    def existing_configurations(self, prefix, **kwargs):
        return (c for c in self.all_configurations(prefix)
                if (self._settings.basedir / c).exists())
