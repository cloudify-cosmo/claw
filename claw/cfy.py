########
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
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

import sys

import sh


def bake(cmd):
    return cmd.bake(_out=lambda line: sys.stdout.write(line),
                    _err=lambda line: sys.stderr.write(line))


try:
    from cloudify_cli.utils import load_cloudify_working_dir_settings
    NEW_CLI = False
    get_profile_context = None
except ImportError:
    load_cloudify_working_dir_settings = None
    from cloudify_cli.env import get_profile_context
    NEW_CLI = True


cfy = bake(sh.cfy)


def teardown(force, ignore_deployments):
    cfy.teardown(force=force, ignore_deployments=ignore_deployments).wait()


def blueprints_delete(blueprint_id):
    if NEW_CLI:
        cfy.blueprints.delete(blueprint_id).wait()
    else:
        cfy.blueprints.delete(blueprint_id=blueprint_id).wait()


def deployments_delete(deployment_id, ignore_live_nodes):
    if NEW_CLI:
        cfy.deployments.delete(deployment_id, force=ignore_live_nodes).wait()
    else:
        cfy.deployments.delete(deployment_id=deployment_id,
                               ignore_live_nodes=ignore_live_nodes).wait()


def executions_start(workflow, deployment_id, include_logs, timeout):
    if NEW_CLI:
        cfy.executions.start(workflow,
                             deployment_id=deployment_id,
                             no_logs=not include_logs,
                             timeout=timeout).wait()
    else:
        cfy.executions.start(workflow=workflow,
                             deployment_id=deployment_id,
                             include_logs=include_logs,
                             timeout=timeout).wait()


def blueprints_upload(blueprint_path, blueprint_id):
    if NEW_CLI:
        cfy.blueprints.upload(blueprint_path, blueprint_id=blueprint_id).wait()
    else:
        cfy.blueprints.upload(blueprint_path=blueprint_path,
                              blueprint_id=blueprint_id).wait()


def deployments_create(blueprint_id, deployment_id, inputs):
    if NEW_CLI:
        cfy.deployments.create(deployment_id,
                               blueprint_id=blueprint_id,
                               inputs=inputs).wait()
    else:
        cfy.deployments.create(deployment_id=deployment_id,
                               blueprint_id=blueprint_id,
                               inputs=inputs).wait()


def init(conf):
    if NEW_CLI:
        pass
    else:
        cfy.init()
        with conf.patch.cli_config as patch:
            patch.obj['colors'] = True


def bootstrap(blueprint_path, inputs):
    if NEW_CLI:
        cfy.bootstrap(blueprint_path, inputs=inputs).wait()
    else:
        cfy.bootstrap(blueprint_path=blueprint_path, inputs=inputs).wait()


def get_manager_ip():
    if NEW_CLI:
        profile = get_profile_context()
        return profile.manager_ip
    else:
        cli_settings = load_cloudify_working_dir_settings()
        return cli_settings.get_management_server()


def get_manager_user():
    if NEW_CLI:
        profile = get_profile_context()
        return profile.manager_user
    else:
        cli_settings = load_cloudify_working_dir_settings()
        return cli_settings.get_management_user()


def get_manager_key():
    if NEW_CLI:
        profile = get_profile_context()
        return profile.manager_key
    else:
        cli_settings = load_cloudify_working_dir_settings()
        return cli_settings.get_management_key()
