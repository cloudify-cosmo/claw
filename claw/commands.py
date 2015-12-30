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

import cosmo_tester
from cloudify_cli import exec_env
from cloudify_cli.execution_events_fetcher import ExecutionEventsFetcher
from cloudify_cli.utils import load_cloudify_working_dir_settings
from cosmo_tester.framework import util

from claw import patcher
from claw import resources
from claw.state import current_configuration
from claw.configuration import Configuration, CURRENT_CONFIGURATION
from claw.settings import settings
from claw.completion import completion
from claw import overview as _overview


INIT_EXISTS = argh.CommandError('Configuration already exists. Use --reset'
                                ' to overwrite.')
NO_INIT = argh.CommandError('Not initialized')
ALREADY_INITIALIZED = argh.CommandError('Already initialized')
NO_BOOTSTRAP = argh.CommandError('Not bootstrapped')
NO_SUCH_CONFIGURATION = argh.CommandError('No such configuration')
STOP_DEPLOYMENT_ENVIRONMENT = '_stop_deployment_environment'


def bake(cmd):
    return cmd.bake(_out=lambda line: sys.stdout.write(line),
                    _err=lambda line: sys.stderr.write(line))


app = argh.EntryPoint('claw')
command = app
cfy = bake(sh.cfy)


@command
def init(suites_yaml=None,
         basedir=None,
         reset=False):
    """Initialize a claw environment.
    """
    if settings.settings_path.exists() and not reset:
        raise INIT_EXISTS
    if not suites_yaml:
        system_tests_dir = os.path.dirname(os.path.dirname(
            cosmo_tester.__file__))
        suites_yaml = os.path.join(system_tests_dir, 'suites', 'suites',
                                   'suites.yaml')
    suites_yaml = os.path.expanduser(suites_yaml)
    if not os.path.exists(suites_yaml):
        raise argh.CommandError(
            'suites.yaml not found at {0}'.format(suites_yaml))
    if not basedir:
        basedir = os.getcwd()
    settings.write_settings(basedir, suites_yaml)
    settings.user_suites_yaml.write_text(resources.get(
        'templates/suites.template.yaml'))
    settings.blueprints_yaml.write_text(resources.get(
        'templates/blueprints.template.yaml'))
    (settings.basedir / '.gitignore').write_text(resources.get(
        'templates/gitignore.template'))
    settings.configurations.mkdir_p()
    settings.default_scripts_dir.mkdir_p()


@command
@arg('configuration', completer=completion.all_configurations)
@arg('-i', '--inputs-override',
     action='append',
     completer=completion.inputs_override_templates)
@arg('-b', '--manager-blueprint-override',
     action='append',
     completer=completion.manager_blueprint_override_templates)
def generate(configuration,
             inputs_override=None,
             manager_blueprint_override=None,
             reset_config=False):
    """Generate a configuration."""
    conf = Configuration(configuration)
    suites_yaml = settings.load_suites_yaml()
    conf.handler_configuration = _generate_configuration(
        cmd_inputs_override=inputs_override,
        cmd_blueprint_override=manager_blueprint_override,
        conf_obj=conf,
        conf_key='handler_configurations',
        conf_name=configuration,
        conf_additional={'install_manager_blueprint_dependencies': False},
        conf_blueprint_key='manager_blueprint',
        blueprint_dir_name='manager-blueprint',
        blueprint_override_key='manager_blueprint_override',
        blueprint_override_template_key='manager_blueprint_override_templates',
        blueprint_path=conf.manager_blueprint_path,
        reset_conf=reset_config,
        properties=None,
        user_yaml=suites_yaml)
    with settings.configurations:
        if os.path.exists(CURRENT_CONFIGURATION):
            os.remove(CURRENT_CONFIGURATION)
        os.symlink(configuration, CURRENT_CONFIGURATION)


@command
@arg('configuration', completer=completion.existing_configurations)
@arg('blueprint', completer=completion.all_blueprints)
def generate_blueprint(configuration, blueprint, reset=False):
    """Generate a blueprint inside a configuration."""
    conf = Configuration(configuration)
    if not conf.exists():
        raise NO_INIT
    blueprints_yaml = settings.load_blueprints_yaml()
    blueprint = conf.blueprint(blueprint)
    blueprint.blueprint_configuration = _generate_configuration(
        cmd_inputs_override=None,
        cmd_blueprint_override=None,
        conf_obj=blueprint,
        conf_key='blueprints',
        conf_name=blueprint.blueprint_name,
        conf_additional=None,
        conf_blueprint_key='blueprint',
        blueprint_dir_name='blueprint',
        blueprint_override_key='blueprint_override',
        blueprint_override_template_key=None,
        blueprint_path=blueprint.blueprint_path,
        reset_conf=reset,
        properties=conf.properties,
        user_yaml=blueprints_yaml)


def _generate_configuration(cmd_inputs_override,
                            cmd_blueprint_override,
                            conf_obj,
                            conf_key,
                            conf_name,
                            conf_additional,
                            conf_blueprint_key,
                            blueprint_dir_name,
                            blueprint_override_key,
                            blueprint_override_template_key,
                            blueprint_path,
                            reset_conf,
                            properties,
                            user_yaml):
    if conf_name not in user_yaml[conf_key]:
        raise NO_SUCH_CONFIGURATION
    conf = user_yaml[conf_key][conf_name]
    cmd_inputs_override = [user_yaml['inputs_override_templates'][key]
                           for key in (cmd_inputs_override or [])]
    cmd_blueprint_override = [user_yaml[blueprint_override_template_key][key]
                              for key in (cmd_blueprint_override or [])]
    original_inputs_path = os.path.expanduser(conf.get('inputs', ''))
    original_blueprint_path = os.path.expanduser(conf[conf_blueprint_key])
    if conf_obj.exists():
        if reset_conf:
            shutil.rmtree(conf_obj.dir)
        else:
            raise ALREADY_INITIALIZED
    conf_obj.dir.makedirs()
    if not original_inputs_path:
        fd, original_inputs_path = tempfile.mkstemp()
        os.close(fd)
        with open(original_inputs_path, 'w') as f:
            f.write('{}')
    _, tmp_blueprint_path = util.generate_unique_configurations(
        workdir=conf_obj.dir,
        original_inputs_path=original_inputs_path,
        original_manager_blueprint_path=original_blueprint_path,
        manager_blueprint_dir_name=blueprint_dir_name)
    shutil.move(tmp_blueprint_path, blueprint_path)
    conf['inputs'] = str(conf_obj.inputs_path)
    conf[conf_blueprint_key] = str(blueprint_path)
    conf.update(conf_additional or {})
    user_yaml['variables'] = user_yaml.get('variables', {})
    user_yaml['variables']['properties'] = properties or {}
    overrides = [
        (conf_obj.inputs_path, 'inputs_override', cmd_inputs_override),
        (blueprint_path, blueprint_override_key, cmd_blueprint_override)
    ]
    for yaml_path, prop, additional_overrides in overrides:
        unprocessed = conf.pop(prop, {})
        for additional in additional_overrides:
            unprocessed.update(additional)
        override = util.process_variables(user_yaml, unprocessed)
        with patcher.YamlPatcher(yaml_path, default_flow_style=False) as patch:
            for k, v in override.items():
                patch.set_value(k, v)
    return conf


@command
@arg('configuration', completer=completion.existing_configurations)
def status(configuration):
    """See the status of an environment specified by a configuration."""
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
@arg('-i', '--inputs-override',
     action='append',
     completer=completion.inputs_override_templates)
@arg('-b', '--manager-blueprint-override',
     action='append',
     completer=completion.manager_blueprint_override_templates)
def bootstrap(configuration,
              inputs_override=None,
              manager_blueprint_override=None,
              reset_config=False):
    """Bootstrap a configuration based environment."""
    conf = Configuration(configuration)
    if not conf.exists() or reset_config:
        generate(configuration,
                 inputs_override=inputs_override,
                 manager_blueprint_override=manager_blueprint_override,
                 reset_config=reset_config)
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
    """Teardown a configuration based environment."""
    conf = Configuration(configuration)
    if not conf.exists():
        raise NO_INIT
    with conf.dir:
        cfy.teardown(force=True, ignore_deployments=True).wait()


@command
@arg('configuration', completer=completion.existing_configurations)
@arg('blueprint', completer=completion.all_blueprints)
def deploy(configuration, blueprint,
           skip_generation=False,
           reset=False,
           timeout=1800):
    """Deploy (upload, create deployment and install) a blueprint
       in a configuration based environment."""
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
    """Undeploy (uninstall, delete deployment and delete blueprint in a
       configuration based environment."""
    _cleanup_deployments(configuration, cancel_executions, blueprint)


@command
@arg('configuration', completer=completion.existing_configurations)
def cleanup_deployments(configuration, cancel_executions=False):
    """Uninstall and delete all deployments and blueprints in an
       environment."""
    _cleanup_deployments(configuration, cancel_executions)


def _cleanup_deployments(configuration, cancel_executions, blueprint=None):
    conf = Configuration(configuration)
    if not conf.dir.isdir():
        raise NO_INIT
    with conf.dir:
        _wait_for_executions(conf, blueprint, cancel_executions)
        if blueprint:
            deployments = blueprints = [blueprint]
        else:
            deployments = [d.id for d in
                           conf.client.deployments.list(_include=['id'])]
            blueprints = [b.id for b in
                          conf.client.blueprints.list(_include=['id'])]
        _wait_for_executions(conf, blueprint, cancel_executions)
        for deployment_id in deployments:
            try:
                cfy.executions.start(workflow='uninstall',
                                     deployment_id=deployment_id,
                                     include_logs=True).wait()
                _wait_for_executions(conf, deployment_id,
                                     cancel_executions)
                cfy.deployments.delete(deployment_id=deployment_id,
                                       ignore_live_nodes=True).wait()
            except Exception as e:
                conf.logger.warn('Failed cleaning deployment: {0} [1]'.format(
                    deployment_id, e))
        for blueprint_id in blueprints:
            try:
                cfy.blueprints.delete(blueprint_id=blueprint_id).wait()
            except Exception as e:
                conf.logger.warn('Failed cleaning blueprint: {0} [1]'.format(
                    blueprint_id, e))


def _wait_for_executions(conf, deployment_id, cancel_executions):
    client = conf.client
    executions = client.executions.list(deployment_id,
                                        include_system_workflows=True)
    for e in executions:
        if e.status in e.END_STATES:
            continue
        if e.workflow_id != STOP_DEPLOYMENT_ENVIRONMENT and cancel_executions:
            client.executions.cancel(e.id)
        while e.status not in e.END_STATES:
            conf.logger.info("Waiting for execution {0}[{1}] to end. "
                             "Current status is {2}".format(e.id,
                                                            e.workflow_id,
                                                            e.status))
            time.sleep(1)
            e = client.executions.get(e.id)


@command
@arg('configuration', completer=completion.all_configurations)
def cleanup(configuration):
    """Clean all infrastructure in a configuration based environment."""
    conf = Configuration(configuration)
    temp_configuration = False
    if not conf.exists():
        temp_configuration = True
        generate(configuration)
    try:
        conf.claw_handler.cleanup()
    finally:
        if temp_configuration:
            conf.dir.rmtree_p()


@command
@arg('configuration', completer=completion.existing_configurations)
def overview(configuration, port=8080):
    """Work in progress."""
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
    """Dump events of an execution in a configuration based environment in
       json format."""
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
            conf.logger.debug('Fetched: {0}'.format(len(self.events)))
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
    """Run a script managed by claw with the provided configuration
       as context."""
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
        current_configuration.set(conf)
        argh.dispatch_command(script_func, argv=script_args)
    finally:
        current_configuration.clear()


@command
def generate_script(script_path, rewrite=False):
    """Generate a scaffold script."""
    if os.path.exists(script_path) and not rewrite:
        raise argh.CommandError('{0} already exists'.format(script_path))
    with open(script_path, 'w') as f:
        f.write(resources.get('templates/script.template.py'))
    os.chmod(script_path, 0755)
