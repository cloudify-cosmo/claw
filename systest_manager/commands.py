import json
import sys
import os
import shutil
import tempfile
import time

import argh
import sh
import requests
from argh.decorators import arg

from cloudify_cli import exec_env
from cloudify_cli.execution_events_fetcher import ExecutionEventsFetcher
from cloudify_cli.utils import load_cloudify_working_dir_settings
from cosmo_tester.framework import util

from systest_manager import resources
from systest_manager.state import current_conf
from systest_manager.configuration import Configuration
from systest_manager.settings import Settings
from systest_manager.completion import Completion
from systest_manager import overview as _overview


CURRENT_CONFIGURATION = '+'
NO_INIT = argh.CommandError('Not initialized')
NO_BOOTSTRAP = argh.CommandError('Not bootstrapped')
STOP_DEPLOYMENT_ENVIRONMENT = '_stop_deployment_environment'


def bake(cmd):
    return cmd.bake(_out=lambda line: sys.stdout.write(line),
                    _err=lambda line: sys.stderr.write(line))


app = argh.EntryPoint('systest')
command = app
cfy = bake(sh.cfy)
settings = Settings()
completion = Completion(settings)


@command
@arg('--basedir', required=True)
@arg('--main_suites_yaml', required=True)
@arg('--user_suites_yaml', required=True)
@arg('--blueprints_yaml', required=False)
def init(basedir=None,
         main_suites_yaml=None,
         user_suites_yaml=None,
         blueprints_yaml=None):
    settings.write_settings(basedir,
                            main_suites_yaml,
                            user_suites_yaml,
                            blueprints_yaml)


@command
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
    handler_configuration['install_manager_blueprint_dependencies'] = False

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

    with settings.basedir:
        if os.path.exists(CURRENT_CONFIGURATION):
            os.remove(CURRENT_CONFIGURATION)
        os.symlink(configuration, CURRENT_CONFIGURATION)


@command
@arg('configuration', completer=completion.existing_configurations)
def status(configuration):
    conf = Configuration(configuration)
    if not conf.exists():
        raise NO_INIT
    with conf.dir:
        manager_ip = conf.handler_configuration.get('manager_ip')
    if not manager_ip:
        raise NO_BOOTSTRAP
    try:
        version = conf.client.manager.get_version()['version']
        return '[{0}] Running ({1})'.format(manager_ip, version)
    except requests.exceptions.ConnectionError:
        raise argh.CommandError('[{0}] Not reachable'.format(manager_ip))


@command
@arg('configuration', completer=completion.all_configurations)
def bootstrap(configuration, reset_config=False):
    conf = Configuration(configuration)
    if not conf.exists() or reset_config:
        generate(configuration, reset_config=reset_config)
    with conf.dir:
        cfy.init().wait()
        with conf.patch.cli_config as patch:
            patch.obj['colors'] = True
        cfy.bootstrap(blueprint_path=conf.manager_blueprint_path,
                      inputs=conf.inputs_path).wait()
        cli_settings = load_cloudify_working_dir_settings()
        with conf.patch.handler_configuration as patch:
            patch.obj.update({
                'manager_ip': cli_settings.get_management_server(),
                'manager_key': cli_settings.get_management_key(),
                'manager_user': cli_settings.get_management_user()
            })


@command
@arg('configuration', completer=completion.existing_configurations)
def teardown(configuration):
    conf = Configuration(configuration)
    if not conf.exists():
        raise NO_INIT
    with conf.dir:
        cfy.teardown(force=True, ignore_deployments=True).wait()


@command
@arg('configuration', completer=completion.existing_configurations)
@arg('blueprint', completer=completion.all_blueprints)
def generate_blueprint(configuration, blueprint, reset=False):
    conf = Configuration(configuration)
    if not conf.exists():
        raise NO_INIT
    blueprints_yaml = settings.load_blueprints_yaml()
    blueprint = conf.blueprint(blueprint)
    if blueprint.dir.exists() and reset:
        shutil.rmtree(blueprint.dir)
    blueprint.dir.makedirs()
    blueprint_configuration = blueprints_yaml['blueprints'][
        blueprint.blueprint_name]
    original_inputs_path = os.path.expanduser(
        blueprint_configuration.get('inputs', ''))
    original_blueprint_path = os.path.expanduser(
        blueprint_configuration['blueprint'])

    if not original_inputs_path:
        _, original_inputs_path = tempfile.mkstemp()
        with open(original_inputs_path, 'w') as f:
            f.write('{}')

    _, blueprint_path = util.generate_unique_configurations(
        workdir=blueprint.dir,
        original_inputs_path=original_inputs_path,
        original_manager_blueprint_path=original_blueprint_path,
        manager_blueprint_dir_name='blueprint')
    shutil.move(blueprint_path, blueprint.blueprint_path)

    blueprint_configuration['inputs'] = str(blueprint.inputs_path)
    blueprint_configuration['blueprint'] = str(blueprint.blueprint_path)

    blueprints_yaml['variables']['properties'] = conf.properties

    def apply_override_and_remove_prop(yaml_path, prop):
        with util.YamlPatcher(yaml_path, default_flow_style=False) as patch:
            override = util.process_variables(
                blueprints_yaml, blueprint_configuration.get(prop, {}))
            for key, value in override.items():
                patch.set_value(key, value)
        if prop in blueprint_configuration:
            del blueprint_configuration[prop]

    apply_override_and_remove_prop(blueprint.inputs_path, 'inputs_override')
    apply_override_and_remove_prop(blueprint.blueprint_path,
                                   'blueprint_override')

    blueprint.blueprint_configuration = blueprint_configuration


@command
@arg('configuration', completer=completion.existing_configurations)
@arg('blueprint', completer=completion.all_blueprints)
def deploy(configuration, blueprint,
           skip_generation=False,
           reset=False,
           timeout=1800):
    conf = Configuration(configuration)
    if not conf.dir.isdir():
        raise NO_INIT
    bp = conf.blueprint(blueprint)
    if not skip_generation:
        generate_blueprint(configuration, blueprint, reset)
    with conf.dir:
        cfy.blueprints.upload(blueprint_path=bp.blueprint_path,
                              blueprint_id=blueprint).wait()
        cfy.deployments.create(blueprint_id=blueprint,
                               deployment_id=blueprint,
                               inputs=bp.inputs_path).wait()
        cfy.executions.start(workflow='install',
                             deployment_id=blueprint,
                             include_logs=True,
                             timeout=timeout).wait()


@command
@arg('configuration', completer=completion.existing_configurations)
@arg('blueprint', completer=completion.all_blueprints)
def undeploy(configuration, blueprint, cancel_executions=False):
    _cleanup_deployments(configuration, cancel_executions, blueprint)


@command
@arg('configuration', completer=completion.existing_configurations)
def cleanup_deployments(configuration, cancel_executions=False):
    _cleanup_deployments(configuration, cancel_executions)


def _cleanup_deployments(configuration, cancel_executions, blueprint=None):
    conf = Configuration(configuration)
    if not conf.dir.isdir():
        raise NO_INIT
    with conf.dir:
        _wait_for_executions(conf.client, blueprint, cancel_executions)
        if blueprint:
            deployments = blueprints = [blueprint]
        else:
            deployments = [d.id for d in
                           conf.client.deployments.list(_include=['id'])]
            blueprints = [b.id for b in
                          conf.client.blueprints.list(_include=['id'])]
        _wait_for_executions(conf.client, blueprint, cancel_executions)
        for deployment_id in deployments:
            cfy.executions.start(workflow='uninstall',
                                 deployment_id=deployment_id,
                                 include_logs=True).wait()
            _wait_for_executions(conf.client, deployment_id, cancel_executions)
            cfy.deployments.delete(deployment_id=deployment_id,
                                   ignore_live_nodes=True).wait()
        for blueprint_id in blueprints:
            cfy.blueprints.delete(blueprint_id=blueprint_id).wait()


def _wait_for_executions(client, deployment_id, cancel_executions):
    executions = client.executions.list(deployment_id,
                                        include_system_workflows=True)
    for e in executions:
        if e.status in e.END_STATES:
            continue
        if e.workflow_id != STOP_DEPLOYMENT_ENVIRONMENT and cancel_executions:
            client.executions.cancel(e.id)
        while e.status not in e.END_STATES:
            print "Waiting for execution {0}[{1}] to end. " \
                  "Current status is {2}".format(e.id,
                                                 e.workflow_id,
                                                 e.status)
            time.sleep(1)
            e = client.executions.get(e.id)


@command
@arg('configuration', completer=completion.all_configurations)
def cleanup(configuration):
    conf = Configuration(configuration)
    temp_configuration = False
    if not conf.exists():
        temp_configuration = True
        generate(configuration)
    try:
        conf.systest_handler.cleanup()
    finally:
        if temp_configuration:
            conf.dir.rmtree_p()


@command
@arg('configuration', completer=completion.existing_configurations)
def overview(configuration, port=8080):
    conf = Configuration(configuration)
    if not conf.exists():
        raise NO_INIT
    _overview.serve(conf, port)


@command
@arg('configuration', completer=completion.existing_configurations)
def events(configuration,
           execution_id,
           output=None,
           batch_size=1000,
           include_logs=False,
           timeout=3600):
    conf = Configuration(configuration)
    if not conf.exists():
        raise NO_INIT
    fetcher = ExecutionEventsFetcher(execution_id=execution_id,
                                     client=conf.client,
                                     batch_size=batch_size,
                                     include_logs=include_logs)

    class Handler(object):
        def __init__(self):
            self.events = []

        def handle(self, batch):
            self.events += batch
            print 'Fetched: {0}'.format(len(self.events))
    handler = Handler()

    fetcher.fetch_and_process_events(events_handler=handler.handle,
                                     timeout=timeout)

    events_json = json.dumps(handler.events)
    if not output:
        sys.stdout.write(events_json)
    else:
        with open(output, 'w') as f:
            f.write(events_json)


@command
@arg('configuration', completer=completion.existing_configurations)
@arg('script_path', completer=completion.script_paths)
@arg('script_args', nargs='...')
def script(configuration, script_path, script_args):
    conf = Configuration(configuration)
    if not conf.exists():
        raise NO_INIT
    if not os.path.isfile(script_path):
        for scripts_dir in settings.scripts:
            possible_script_path = scripts_dir / script_path
            if possible_script_path.isfile():
                script_path = possible_script_path
                break
        else:
            raise argh.CommandError('Could not locate {0}'.format(script_path))
    exec_globs = exec_env.exec_globals(script_path)
    execfile(script_path, exec_globs)
    if script_args and script_args[0] in exec_globs:
        func = script_args[0]
        script_args = script_args[1:]
    else:
        func = 'script'
    script_func = exec_globs.get(func)
    if not script_func:
        raise argh.CommandError('Cannot find a function to execute. Did you '
                                'add a default "script" function?')
    try:
        current_conf.set(conf)
        argh.dispatch_command(script_func, argv=script_args)
    finally:
        current_conf.clear()


@command
def generate_script(script_path, rewrite=False):
    if os.path.exists(script_path) and not rewrite:
        raise argh.CommandError('{0} already exists'.format(script_path))
    with open(script_path, 'w') as f:
        f.write(resources.get('templates/script.template.py'))
    os.chmod(script_path, 0755)
