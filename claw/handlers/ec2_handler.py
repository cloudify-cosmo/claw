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
            instance.terminate()
        while self.ec2.get_all_reservations():
            self.logger.info('Waiting for all EC2 instances to terminate...')
            time.sleep(5)


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
