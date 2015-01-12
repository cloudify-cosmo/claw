import sys
import os
import shutil
import errno

import argh
import sh
import yaml
from path import path
from argh.decorators import arg

from cosmo_tester.framework import util


def sh_bake(command):
    return command.bake(_out=lambda line: sys.stdout.write(line),
                        _err=lambda line: sys.stderr.write(line))


class Settings(object):

    systest_settings = path(
        os.path.expanduser(os.environ.get('SYSTEST_SETTINGS',
                                          '~/.cloudify-systest')))

    def __init__(self):
        self._settings = None

    @property
    def main_suites_yaml(self):
        self._load_settings()
        return path(self._settings['main_suites_yaml'])

    @property
    def user_suites_yaml(self):
        self._load_settings()
        return path(self._settings['user_suites_yaml'])

    @property
    def basedir(self):
        self._load_settings()
        return path(self._settings['basedir'])

    def _load_settings(self):
        if self._settings:
            return
        if not self.systest_settings.exists():
            raise argh.CommandError('Run `systest init` to configure systest')
        self._settings = yaml.safe_load(self.systest_settings.text())

    def write_settings(self,
                       basedir,
                       main_suites_yaml_path,
                       user_suites_yaml_path):
        self.systest_settings.write_text(yaml.safe_dump({
            'basedir': os.path.expanduser(basedir),
            'main_suites_yaml': os.path.expanduser(main_suites_yaml_path),
            'user_suites_yaml': os.path.expanduser(user_suites_yaml_path)
        }, default_flow_style=False))

    def load_suites_yaml(self, variables=True):
        suites_yaml = yaml.load(self.user_suites_yaml.text())
        if variables:
            main_suites_yaml = yaml.load(self.main_suites_yaml.text())
            variables = main_suites_yaml.get('variables', {})
            variables.update(suites_yaml.get('variables', {}))
            suites_yaml['variables'] = variables
        return suites_yaml


class Completion(object):

    def __init__(self, settings):
        self._settings = settings

    def _configurations(self):
        return settings.load_suites_yaml(variables=False)[
            'handler_configurations'].keys()

    def all_configurations(self, prefix, **kwargs):
        return (c for c in self._configurations()
                if c.startswith(prefix))

    def existing_configurations(self, prefix, **kwargs):
        return (c for c in self._configurations()
                if c.startswith(prefix) and
                (self._settings.basedir / c).exists())


cfy = sh_bake(sh.cfy)
settings = Settings()
completion = Completion(settings)


@arg('--basedir', required=True)
@arg('--main_suites_yaml', required=True)
@arg('--user_suites_yaml', required=True)
def init(basedir=None, main_suites_yaml=None, user_suites_yaml=None):
    settings.write_settings(basedir, main_suites_yaml, user_suites_yaml)


@arg('configuration', completer=completion.all_configurations)
def generate(configuration, reset_config=False):
    suites_yaml = settings.load_suites_yaml()
    handler_configuration = suites_yaml[
        'handler_configurations'][configuration]
    original_inputs_path = os.path.expanduser(handler_configuration['inputs'])
    original_manager_blueprint_path = os.path.expanduser(
        handler_configuration['manager_blueprint'])
    handler_configuration_dir = settings.basedir / configuration
    if reset_config and handler_configuration_dir.exists():
        shutil.rmtree(handler_configuration_dir)
    handler_configuration_dir.makedirs()

    inputs_path, manager_blueprint_path = util.generate_unique_configurations(
        workdir=handler_configuration_dir,
        original_inputs_path=original_inputs_path,
        original_manager_blueprint_path=original_manager_blueprint_path)
    inputs_path = str(inputs_path)
    new_manager_blueprint_path = (
        manager_blueprint_path.dirname() / 'manager-blueprint.yaml')
    shutil.move(manager_blueprint_path, new_manager_blueprint_path)
    manager_blueprint_path = str(new_manager_blueprint_path)

    handler_configuration_path = (
        handler_configuration_dir / 'handler-configuration.yaml')
    handler_configuration['inputs'] = inputs_path
    handler_configuration['manager_blueprint'] = manager_blueprint_path

    def apply_override_and_remove_prop(yaml_path, prop):
        with util.YamlPatcher(yaml_path, default_flow_style=False) as patch:
            override = util.process_variables(
                suites_yaml, handler_configuration.get(prop, {}))
            for key, value in override.items():
                patch.set_value(key, value)
        if prop in handler_configuration:
            del handler_configuration[prop]

    apply_override_and_remove_prop(inputs_path, 'inputs_override')
    apply_override_and_remove_prop(manager_blueprint_path,
                                   'manager_blueprint_override')

    handler_configuration_path.write_text(yaml.dump(handler_configuration,
                                                    default_flow_style=False))


@arg('configuration', completer=completion.existing_configurations)
def status(configuration):
    try:
        with settings.basedir / configuration:
            cfy.status().wait()
    except sh.ErrorReturnCode:
        pass
    except OSError as e:
        if e.errno == errno.ENOENT:
            return 'Not initialized'
        raise


@arg('configuration', completer=completion.all_configurations)
def bootstrap(configuration, reset_config=False):
    config_dir = settings.basedir / configuration
    if not config_dir.exists() or reset_config:
        generate(configuration, reset_config=reset_config)
    with config_dir:
        blueprint_path = (
            config_dir / 'manager-blueprint' / 'manager-blueprint.yaml')
        cfy.init().wait()
        cfy.bootstrap(blueprint_path=blueprint_path,
                      inputs=config_dir / 'inputs.yaml').wait()


@arg('configuration', completer=completion.existing_configurations)
def teardown(configuration):
    config_dir = settings.basedir / configuration
    if not config_dir.exists():
        'Not initialized'
    with config_dir:
        cfy.teardown(force=True, ignore_deployments=True).wait()


def global_status():
    for directory in settings.basedir.dirs():
        configuration = directory.basename()
        print 'Configuration: {0}'.format(configuration)
        config_status = status(directory.basename())
        if config_status:
            print config_status


commands = (init, generate, status, bootstrap, teardown, global_status)
