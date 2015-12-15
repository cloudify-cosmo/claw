import os

import bottle

from systest_manager import resources


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
                {'id': 1, 'author': "Pete Hunt", 'text': "This is one comment"},
                {'id': 2, 'author': "Jordan Walk!", 'text': "This is *another* comment"}
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
