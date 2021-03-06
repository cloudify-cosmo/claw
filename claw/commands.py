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
import shutil
import sys
import tempfile
import time

import argh
import requests
from argh.decorators import arg

import cosmo_tester
from cosmo_tester.framework import util

from claw import cfy
from claw import exec_env
from claw import patcher
from claw import resources
from claw.state import current_configuration
from claw.configuration import Configuration, CURRENT_CONFIGURATION
from claw.settings import settings
from claw.completion import completion

INIT_EXISTS = argh.CommandError('Configuration already exists. Use --reset'
                                ' to overwrite.')
NO_INIT = argh.CommandError('Not initialized')
ALREADY_INITIALIZED = argh.CommandError('Configuration already initialized. '
                                        'Use --reset to overwrite.')
NO_BOOTSTRAP = argh.CommandError('Configuration not bootstrapped.')
NO_SUCH_CONFIGURATION = argh.CommandError('No such configuration.')
STOP_DEPLOYMENT_ENVIRONMENT = '_stop_deployment_environment'


app = argh.EntryPoint('claw')
command = app


@command
def init(suites_yaml=None,
         claw_home=None,
         reset=False):
    """Initialize a claw environment."""
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
    if not claw_home:
        claw_home = os.getcwd()
    settings.write_settings(claw_home, suites_yaml)
    settings.user_suites_yaml.write_text(resources.get(
        'templates/suites.template.yaml'))
    settings.blueprints_yaml.write_text(resources.get(
        'templates/blueprints.template.yaml'))
    (settings.claw_home / '.gitignore').write_text(resources.get(
        'templates/gitignore.template'))
    settings.configurations.mkdir_p()
    settings.default_scripts_dir.mkdir_p()
    generate_script(settings.default_scripts_dir / 'example-script.py',
                    reset=True)


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
             reset=False):
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
        reset=reset,
        properties=None,
        user_yaml=suites_yaml)
    with settings.configurations:
        if os.path.islink(CURRENT_CONFIGURATION):
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
        reset=reset,
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
                            reset,
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
    if conf_obj.dir.exists():
        if reset:
            if conf_obj.dir == os.getcwd():
                os.chdir(conf_obj.dir.dirname())
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
    manager_ip = conf.handler_configuration.get('manager_ip')
    if not manager_ip:
        raise NO_BOOTSTRAP
    try:
        version = conf.client.manager.get_version()['version']
        conf.logger.info('[{0}] Running ({1})'.format(manager_ip, version))
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
              reset=False):
    """Bootstrap a configuration based environment."""
    conf = Configuration(configuration)
    if not conf.exists() or reset:
        generate(configuration=configuration,
                 inputs_override=inputs_override,
                 manager_blueprint_override=manager_blueprint_override,
                 reset=reset)
    with conf.dir:
        cfy.init(conf)
        cfy.bootstrap(blueprint_path=conf.manager_blueprint_path,
                      inputs=conf.inputs_path)
        with conf.patch.handler_configuration as patch:
            patch.obj.update({
                'manager_ip': cfy.get_manager_ip(),
                'manager_key': cfy.get_manager_key(),
                'manager_user': cfy.get_manager_user()
            })


@command
@arg('configuration', completer=completion.existing_configurations)
def teardown(configuration):
    """Teardown a configuration based environment."""
    conf = Configuration(configuration)
    if not conf.exists():
        raise NO_INIT
    with conf.dir:
        cfy.teardown(force=True, ignore_deployments=True)


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
        generate_blueprint(configuration=configuration,
                           blueprint=blueprint,
                           reset=reset)
    with conf.dir:
        cfy.blueprints_upload(blueprint_path=bp.blueprint_path,
                              blueprint_id=blueprint)
        cfy.deployments_create(blueprint_id=blueprint,
                               deployment_id=blueprint,
                               inputs=bp.inputs_path)
        cfy.executions_start(workflow='install',
                             deployment_id=blueprint,
                             include_logs=True,
                             timeout=timeout)


@command
@arg('configuration', completer=completion.existing_configurations)
@arg('blueprint', completer=completion.existing_blueprints)
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
                cfy.executions_start(workflow='uninstall',
                                     deployment_id=deployment_id,
                                     include_logs=True,
                                     timeout=1800)
                _wait_for_executions(conf, deployment_id,
                                     cancel_executions)
                cfy.deployments_delete(deployment_id=deployment_id,
                                       ignore_live_nodes=True)
            except Exception as e:
                conf.logger.warn('Failed cleaning deployment: {0} [1]'.format(
                    deployment_id, e))
        for blueprint_id in blueprints:
            try:
                cfy.blueprints_delete(blueprint_id=blueprint_id)
            except Exception as e:
                conf.logger.warn('Failed cleaning blueprint: {0} [1]'.format(
                    blueprint_id, e))


def _wait_for_executions(conf, deployment_id, cancel_executions):
    client = conf.client
    executions = client.executions.list(deployment_id,
                                        include_system_workflows=True)
    for e in executions:
        if e.status in e.END_STATES:
            if (cancel_executions and
                    e.workflow_id == 'create_deployment_environment'):
                conf.client.executions.update(e.id, status=e.TERMINATED)
            continue
        if e.workflow_id != STOP_DEPLOYMENT_ENVIRONMENT and cancel_executions:
            client.executions.cancel(e.id)
        cancel_timeout = time.time() + 10
        while e.status not in e.END_STATES and time.time() < cancel_timeout:
            conf.logger.info('Waiting for execution {0}[{1}] to end. '
                             'Current status is {2}'.format(e.id,
                                                            e.workflow_id,
                                                            e.status))
            time.sleep(1)
            e = client.executions.get(e.id)
        if cancel_executions and e.status not in e.END_STATES:
            if e.workflow_id == 'create_deployment_environment':
                new_status = e.TERMINATED
            else:
                new_status = e.CANCELLED
            conf.logger.info('Execution did not reach a final state. '
                             'Manually setting status: {0}'.format(new_status))
            client.executions.update(e.id, status=new_status)


@command
@arg('configuration', completer=completion.all_configurations)
@arg('-i', '--inputs-override',
     action='append',
     completer=completion.inputs_override_templates)
@arg('-b', '--manager-blueprint-override',
     action='append',
     completer=completion.manager_blueprint_override_templates)
def cleanup(configuration,
            inputs_override=None,
            manager_blueprint_override=None):
    """Clean all infrastructure in a configuration based environment."""
    conf = Configuration(configuration)
    temp_configuration = False
    if not conf.exists():
        temp_configuration = True
        generate(configuration,
                 inputs_override=inputs_override,
                 manager_blueprint_override=manager_blueprint_override)
    if not temp_configuration and (inputs_override or
                                   manager_blueprint_override):
        conf.logger.warn('Inputs override or manager blueprints override '
                         'was passed, but an existing configuration was '
                         'found so they are ignored and the existing '
                         'configuration will be used.')
    try:
        conf.claw_handler.cleanup()
    finally:
        if temp_configuration:
            conf.dir.rmtree_p()
            with settings.configurations:
                if os.path.islink(CURRENT_CONFIGURATION):
                    os.remove(CURRENT_CONFIGURATION)


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
            possible_script_path2 = scripts_dir / '{0}.py'.format(script_path)
            if possible_script_path.isfile():
                script_path = possible_script_path
                break
            if possible_script_path2.isfile():
                script_path = possible_script_path2
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


def add_script_based_commands():
    names = {getattr(f, argh.decorators.ATTR_NAME,
                     f.__name__.replace('_', '-')) for f in app.commands}

    def _gen_func(script_path):
        name = script_path.basename()[:-len('.py')].replace('_', '-')
        if name in names:
            raise argh.CommandError('Name conflict: Found two commands named '
                                    '"{0}".'.format(name))

        @command
        @arg('configuration', completer=completion.existing_configurations)
        @arg('script_args', nargs='...')
        @argh.named(name)
        def func(configuration, script_args):
            """Script based command."""
            return script(configuration, script_path, script_args)
        return func
    for scripts_dir in settings.scripts:
        for script_file in scripts_dir.files('*.py'):
            _gen_func(script_file)


@command
def generate_script(script_path, reset=False, plain=False):
    """Generate a scaffold script."""
    if os.path.exists(script_path) and not reset:
        raise argh.CommandError('{0} already exists'.format(script_path))
    template = 'script.plain.template.py' if plain else 'script.template.py'
    with open(script_path, 'w') as f:
        f.write(resources.get('templates/{0}'.format(template)))
    os.chmod(script_path, os.stat(script_path).st_mode | 0o111)


@command
def cdconfiguration():
    """Output bash function and completion for cdconfiguration."""
    if not settings.settings_path.exists():
        return
    cdconfiguration_template = resources.get(
        'templates/cdconfiguration.template.sh')
    sys.stdout.write(cdconfiguration_template.replace('{{configurations}}',
                                                      settings.configurations))
