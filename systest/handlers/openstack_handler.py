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

import time

import keystoneclient.v2_0.client as keystone_client
import neutronclient.v2_0.client as neutron_client
import cinderclient.v1.client as cinder_client
import novaclient.v2.client as nova_client

from systest import handlers


class CleanupHandler(object):

    def __init__(self, handler):
        configuration = handler.configuration
        self.logger = configuration.logger
        self.should_delete_keypairs = configuration.handler_configuration.get(
            'delete_keypairs', False)
        clients = handler.clients()
        self.keystone = clients['keystone']
        self.neutron = clients['neutron']
        self.nova = clients['nova']
        self.cinder = clients['cinder']

    def cleanup(self):
        self.delete_servers()
        self.delete_keys()
        self.delete_volumes()
        self.delete_routers()
        self.delete_ports()
        self.delete_networks()
        self.delete_security_groups()
        self.delete_floatingips()
        self.logger.info('Done!')

    def delete_servers(self):
        self.logger.info('Deleting Servers')
        for server in self.nova.servers.list():
            self.logger.info('\tDeleting server {0}'.format(server.name))
            self.nova.servers.delete(server.id)

        while self.nova.servers.list():
            self.logger.info('Waiting for all servers to delete...')
            time.sleep(5)

    def delete_keys(self):
        self.logger.info('Deleting Keypairs')
        for keypair in self.nova.keypairs.list():
            if self.should_delete_keypairs:
                self.logger.info('\tDeleting keypair {0}'.format(keypair.name))
                self.nova.keypairs.delete(keypair.id)
            else:
                self.logger.info('\tSkipping keypair {0}'.format(keypair.name))

    def delete_volumes(self):
        self.logger.info('Deleting Volumes')
        for volume in self.cinder.volumes.list():
            self.logger.info('\tdeleting volume {0}'.format(
                volume.display_name))
            self.cinder.volumes.delete(volume.id)

        while self.cinder.volumes.list():
            self.logger.info('Waiting for all volumes to delete...')
            time.sleep(5)

    def delete_routers(self):
        self.logger.info('Deleting Routers')
        for router in self.neutron.list_routers()['routers']:
            for port in self.neutron.list_ports(device_id=router['id'])[
                    'ports']:
                subnet_id = port['fixed_ips'][0]['subnet_id']
                self.logger.info('\tDeleting router interface to subnet ID {0}'
                                 .format(subnet_id))
                self.neutron.remove_interface_router(router['id'],
                                                     {'subnet_id': subnet_id})
            self.logger.info('\tDeleting router {0}'.format(router['name']))
            self.neutron.delete_router(router['id'])

    def delete_ports(self):
        self.logger.info('Deleting Ports')
        for port in self.neutron.list_ports()['ports']:
            self.logger.info('\tDeleting port {0}'.format(port['name']))
            self.neutron.delete_port(port['id'])

    def delete_networks(self):
        self.logger.info('Deleting Networks')
        for network in self.neutron.list_networks()['networks']:
            if not network['router:external']:
                self.logger.info('\tDeleting network {0}'.format(
                    network['name']))
                self.neutron.delete_network(network['id'])

    def delete_security_groups(self):
        self.logger.info('Deleting Security Groups')
        for sg in self.neutron.list_security_groups()['security_groups']:
            if sg['name'] != 'default':
                self.logger.info('\tDeleting security group {0}'.format(
                    sg['name']))
                self.neutron.delete_security_group(sg['id'])

    def delete_floatingips(self):
        self.logger.info('Deleting Floating IPs')
        for fip in self.neutron.list_floatingips()['floatingips']:
            self.logger.info('\tDeleting floating IP {0}'.format(
                fip['floating_ip_address']))
            self.neutron.delete_floatingip(fip['id'])


class Handler(handlers.Handler):

    def cleanup(self):
        CleanupHandler(self).cleanup()

    def clients(self):
        inputs = self.configuration.inputs
        username = inputs['keystone_username']
        password = inputs['keystone_password']
        tenant_name = inputs['keystone_tenant_name']
        region_name = inputs['region']
        auth_url = inputs['keystone_url']
        clients_std_keys_kw = {
            'username': username,
            'password': password,
            'tenant_name': tenant_name,
            'auth_url': auth_url
        }
        clients_old_keys_kw = {
            'username': username,
            'api_key': password,
            'project_id': tenant_name,
            'auth_url': auth_url,
            'region_name': region_name
        }

        keystone = keystone_client.Client(**clients_std_keys_kw)
        clients_std_keys_kw['region_name'] = region_name
        neutron = neutron_client.Client(**clients_std_keys_kw)
        nova = nova_client.Client(**clients_old_keys_kw)
        cinder = cinder_client.Client(**clients_old_keys_kw)

        return {
            'keystone': keystone,
            'neutron': neutron,
            'nova': nova,
            'cinder': cinder
        }
