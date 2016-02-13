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

import time

import boto
import boto.ec2
import boto.vpc
import boto.ec2.elb

from claw import handlers


class CleanupHandler(object):

    def __init__(self, handler):
        configuration = handler.configuration
        self.logger = configuration.logger
        clients = handler.clients()
        self.ec2 = clients['ec2']
        self.vpc = clients['vpc']
        self.elb = clients['elb']

    def cleanup(self):
        self.delete_instances()
        self.logger.info('Done!')

    def delete_instances(self):
        self.logger.info('Terminating EC2 Instances')
        for reservation in self.ec2.get_all_reservations():
            instance = reservation.instances[0]
            self.logger.info('\tTerminating instance: {}'.format(instance.id))
            instance.terminate()
        while self.ec2.get_all_reservations():
            self.logger.info('Waiting for all EC2 instances to terminate...')
            time.sleep(5)

    def delete_keypairs(self):
        self.logger.info('Deleting Key Pairs')
        for keypair in self.ec2.get_all_keypairs():
            self.logger.info('\tDeleting key pair {}'.format(keypair.name))
            self.ec2.delete_key_pair(keypair)

    def delete_elasticips(self):
        self.logger.info('Releasing Elastic IPs')
        for address in self.ec2.get_all_addresses():
            self.logger.info('\tReleasing elastic ip {}'.format(
                address.public_ip))
            address.release()

    def delete_security_groups(self):
        self.logger.info('Deleting security groups')
        for security_group in self.ec2.get_all_security_groups():
            if 'default' in security_group.name:
                continue
            self.logger.info('\tDeleting security group {}'.format(
                security_group.name))
            security_group.delete()

    def delete_volumes(self):
        self.logger.info('Deleting volumes')
        for volume in self.ec2.get_all_volumes():
            if volume.status == 'in-use':
                self.logger.info('\tDetaching volume {}'.format(volume.id))
                volume.detach(force=True)
            self.logger.info('\tDeleting volume {}'.format(volume.id))
            volume.delete()

    def delete_snapshots(self):
        self.logger.info('Deleting snapshots')
        for snapshot in self.ec2.get_all_snapshots(owner='self'):
            self.logger.info('\tDeleting snapshot {}'.format(snapshot.id))
            snapshot.delete()

    def delete_load_balancers(self):
        self.logger.info('Deleting load balancers')
        for elb in self.elb.get_all_load_balancers():
            self.logger.info('\tDeleting load balancer {}'.format(elb.name))
            elb.delete()

    def delete_vpcs(self):
        pass

    def delete_subnets(self):
        pass

    def delete_internet_gateways(self):
        pass

    def delete_vpn_gateways(self):
        pass

    def delete_customer_gateways(self):
        pass

    def delete_network_acls(self):
        pass

    def delete_dhcp_option_sets(self):
        pass

    def delete_route_tables(self):
        pass


class Handler(handlers.Handler):

    def cleanup(self):
        CleanupHandler(self).cleanup()

    def clients(self):
        inputs = self.configuration.inputs
        credentials = {
            'aws_access_key_id': inputs['aws_access_key_id'],
            'aws_secret_access_key': inputs['aws_secret_access_key'],
            'region': boto.ec2.get_region(inputs['ec2_region_name'])
        }
        return {
            'ec2': boto.ec2.EC2Connection(**credentials),
            'vpc': boto.vpc.VPCConnection(**credentials),
            'elb': boto.ec2.elb.ELBConnection(**credentials)
        }
