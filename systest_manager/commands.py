import sys
import os
import shutil

import argh
import sh
import yaml
import requests
from argh.decorators import arg

import cloudify_cli
from cloudify_rest_client import CloudifyClient
from cloudify_cli.utils import load_cloudify_working_dir_settings
from cosmo_tester.framework import util

from settings import Settings
from completion import Completion


NO_INIT = 'Not initialized'
NO_BOOTSTRAP = 'Not bootstrapped'


def get_manager_ip():
    cli_settings = load_cloudify_working_dir_settings()
    return cli_settings.get_management_server()


app = argh.EntryPoint('systest')
cfy = sh.cfy.bake(_out=lambda line: sys.stdout.write(line),
                  _err=lambda line: sys.stderr.write(line))
settings = Settings()
completion = Completion(settings)


@app
@arg('--basedir', required=True)
@arg('--main_suites_yaml', required=True)
@arg('--user_suites_yaml', required=True)
def init(basedir=None, main_suites_yaml=None, user_suites_yaml=None):
    settings.write_settings(basedir, main_suites_yaml, user_suites_yaml)


@app
@arg('configuration', completer=completion.all_configurations)
def generate(configuration, reset_config=False):
    suites_yaml = settings.load_suites_yaml()
    handler_configuration = suites_yaml[
        'handler_configurations'][configuration]
    is_manager_bootstrap = not handler_configuration.get(
        'bootstrap_using_providers', False)
    original_inputs_path = os.path.expanduser(handler_configuration['inputs'])
    if is_manager_bootstrap:
        original_manager_blueprint_path = os.path.expanduser(
            handler_configuration['manager_blueprint'])
    else:
        original_manager_blueprint_path = None
    handler_configuration_dir = settings.basedir / configuration
    if reset_config and handler_configuration_dir.exists():
        shutil.rmtree(handler_configuration_dir)
    handler_configuration_dir.makedirs()

    inputs_path, manager_blueprint_path = util.generate_unique_configurations(
        workdir=handler_configuration_dir,
        original_inputs_path=original_inputs_path,
        original_manager_blueprint_path=original_manager_blueprint_path,
        is_provider_bootstrap=not is_manager_bootstrap)
    inputs_path = str(inputs_path)
    if is_manager_bootstrap:
        new_manager_blueprint_path = (
            manager_blueprint_path.dirname() / 'manager-blueprint.yaml')
        shutil.move(manager_blueprint_path, new_manager_blueprint_path)
        manager_blueprint_path = str(new_manager_blueprint_path)

    handler_configuration_path = (
        handler_configuration_dir / 'handler-configuration.yaml')
    handler_configuration['inputs'] = inputs_path
    if is_manager_bootstrap:
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
    if is_manager_bootstrap:
        apply_override_and_remove_prop(manager_blueprint_path,
                                       'manager_blueprint_override')

    handler_configuration_path.write_text(
        yaml.safe_dump(handler_configuration, default_flow_style=False))


@app
@arg('configuration', completer=completion.existing_configurations)
def status(configuration):
    config_dir = settings.basedir / configuration
    if not config_dir.exists():
        return NO_INIT
    try:
        with settings.basedir / configuration:
            manager_ip = get_manager_ip()
        if not manager_ip:
            return NO_BOOTSTRAP
        client = CloudifyClient(manager_ip)
        try:
            version = client.manager.get_version()['version']
            return '[{0}] Running ({1})'.format(manager_ip, version)
        except requests.exceptions.ConnectionError:
            return '[{0}] Not reachable'.format(manager_ip)
    except cloudify_cli.exceptions.CloudifyCliError as e:
        if NO_INIT in str(e):
            return NO_INIT
        else:
            raise


@app
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
        handler_configuration_path = config_dir / 'handler-configuration.yaml'
        handler_configuration = yaml.load(handler_configuration_path.text())
        handler_configuration['manager_ip'] = get_manager_ip()
        handler_configuration_path.write_text(
            yaml.safe_dump(handler_configuration, default_flow_style=False))


@app
@arg('configuration', completer=completion.existing_configurations)
def teardown(configuration):
    config_dir = settings.basedir / configuration
    if not config_dir.exists():
        return NO_INIT
    with config_dir:
        cfy.teardown(force=True, ignore_deployments=True).wait()


@app
def global_status():
    if not settings.basedir.exists():
        return
    for directory in settings.basedir.dirs():
        configuration = directory.basename()
        yield '{0}: {1}'.format(configuration, status(configuration))


@app
def clear(force=False):
    if not force:
        raise argh.CommandError('Must pass -f flag to actually clear '
                                'configurations dir')
    if settings.basedir.exists():
        shutil.rmtree(settings.basedir)
