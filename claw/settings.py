########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
############

import os

import argh
import yaml
from path import path


CLAW_SETTINGS = 'CLAW_SETTINGS'
DEFAULT_SETTINGS_PATH = '~/.claw'
DEFAULT_SCRIPTS_DIR = 'scripts'


class Settings(object):

    def __init__(self):
        self._settings = None

    @property
    def settings_path(self):
        return path(os.path.expanduser(
            os.environ.get(CLAW_SETTINGS, DEFAULT_SETTINGS_PATH)))

    @property
    def claw_home(self):
        return path(self.settings['claw_home'])

    @property
    def configurations(self):
        return self.claw_home / 'configurations'

    @property
    def default_scripts_dir(self):
        return self.claw_home / DEFAULT_SCRIPTS_DIR

    @property
    def user_suites_yaml(self):
        return self.claw_home / 'suites.yaml'

    @property
    def blueprints_yaml(self):
        return self.claw_home / 'blueprints.yaml'

    @property
    def main_suites_yaml(self):
        return path(self.settings['main_suites_yaml'])

    @property
    def scripts(self):
        return [path(scripts_dir) for scripts_dir in self.settings['scripts']]

    @property
    def settings(self):
        if not self.settings_path.exists():
            raise argh.CommandError('Run `claw init` to configure claw')
        if not self._settings:
            self._settings = yaml.safe_load(self.settings_path.text())
        return self._settings

    def write_settings(self,
                       claw_home,
                       main_suites_yaml_path):
        claw_home = os.path.abspath(os.path.expanduser(claw_home))
        default_scripts_dir = os.path.join(claw_home, DEFAULT_SCRIPTS_DIR)
        main_suites_yaml = os.path.abspath(
            os.path.expanduser(main_suites_yaml_path))
        self.settings_path.write_text(yaml.safe_dump({
            'claw_home': claw_home,
            'main_suites_yaml': main_suites_yaml,
            'scripts': [default_scripts_dir]
        }, default_flow_style=False))

    def load_suites_yaml(self, variables=True):
        suites_yaml = yaml.load(self.user_suites_yaml.text())
        if variables:
            main_suites_yaml = yaml.load(self.main_suites_yaml.text())
            variables = main_suites_yaml.get('variables', {})
            variables.update(suites_yaml.get('variables', {}))
            suites_yaml['variables'] = variables
        return suites_yaml

    def load_blueprints_yaml(self, variables=True):
        blueprints_yaml = yaml.load(self.blueprints_yaml.text())
        if variables:
            suites_yaml = self.load_suites_yaml(variables=True)
            variables = suites_yaml['variables']
            variables.update(blueprints_yaml.get('variables', {}))
            blueprints_yaml['variables'] = variables
        return blueprints_yaml
settings = Settings()
