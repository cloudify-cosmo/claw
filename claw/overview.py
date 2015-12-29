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

import bottle

from claw import resources


class Overview(object):

    def __init__(self, configuration):
        self.app = bottle.app()
        self.conf = configuration
        self.client = configuration.client

    @staticmethod
    def static(filename):
        return bottle.static_file(filename,
                                  root=os.path.join(resources.DIR, 'overview'))

    def comments(self):
        return {
            'comments': [
                {'id': 1, 'author': "Pete Hunt", 'text': "Comment 1"},
                {'id': 2, 'author': "Jordan Walk!", 'text': "Comment 2"}
            ]
        }

    def index(self):
        return self.static('index.html')

    def serve(self, port):
        routes = {
            '/': self.index,
            '/comments': self.comments,
            '/static/<filename:path>': self.static,
        }
        for route, handler in routes.items():
            self.app.route(route)(handler)
        self.conf.logger.info('http://localhost:{0}'.format(port))
        self.app.run(debug=True, port=port)


def serve(configuration, port):
    Overview(configuration).serve(port=port)
