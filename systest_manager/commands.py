import sys
import os
import shutil

import argh
import sh
import requests
from argh.decorators import arg

import cloudify_cli
from cloudify_rest_client import CloudifyClient
from cloudify_cli.utils import load_cloudify_working_dir_settings
from cosmo_tester.framework import util

from configuration import Configuration
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
    conf = Configuration(configuration)
    suites_yaml = settings.load_suites_yaml()
    handler_configuration = suites_yaml[
        'handler_configurations'][configuration]
    original_inputs_path = os.path.expanduser(handler_configuration['inputs'])
    original_manager_blueprint_path = os.path.expanduser(
        handler_configuration['manager_blueprint'])
    if reset_config and conf.dir.exists():
        shutil.rmtree(conf.dir)
    conf.dir.makedirs()

    _, manager_blueprint_path = util.generate_unique_configurations(
        workdir=conf.dir,
        original_inputs_path=original_inputs_path,
        original_manager_blueprint_path=original_manager_blueprint_path)
    shutil.move(manager_blueprint_path, conf.manager_blueprint_path)

    handler_configuration['inputs'] = str(conf.inputs_path)
    handler_configuration['manager_blueprint'] = str(
        conf.manager_blueprint_path)

    def apply_override_and_remove_prop(yaml_path, prop):
        with util.YamlPatcher(yaml_path, default_flow_style=False) as patch:
            override = util.process_variables(
                suites_yaml, handler_configuration.get(prop, {}))
            for key, value in override.items():
                patch.set_value(key, value)
        if prop in handler_configuration:
            del handler_configuration[prop]

    apply_override_and_remove_prop(conf.inputs_path, 'inputs_override')
    apply_override_and_remove_prop(conf.manager_blueprint_path,
                                   'manager_blueprint_override')

    conf.handler_configuration = handler_configuration


@app
@arg('configuration', completer=completion.existing_configurations)
def status(configuration):
    conf = Configuration(configuration)
    if not conf.dir.exists():
        return NO_INIT
    try:
        with conf.dir:
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
    conf = Configuration(configuration)
    if not conf.dir.exists() or reset_config:
        generate(configuration, reset_config=reset_config)
    with conf.dir:
        cfy.init().wait()
        cfy.bootstrap(blueprint_path=conf.manager_blueprint_path,
                      inputs=conf.inputs_path).wait()

        handler_configuration = conf.handler_configuration
        handler_configuration['manager_ip'] = get_manager_ip()
        conf.handler_configuration = handler_configuration


@app
@arg('configuration', completer=completion.existing_configurations)
def teardown(configuration):
    conf = Configuration(configuration)
    if not conf.dir.exists():
        return NO_INIT
    with conf.dir:
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
