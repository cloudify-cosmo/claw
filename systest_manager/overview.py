import os

import bottle

from systest_manager import resources


class Overview(object):

    def __init__(self, configuration):
        self.app = bottle.app()
        self.configuration = configuration
        self.client = configuration.client
        self.host = self.client._client.host

    def metadata(self):
        return {
            'version': self.client.manager.get_version()['version'],
            'host': self.host,
            'configuration': self.configuration.configuration
        }

    def state(self):
        deployment_ids = [d.id for d in
                          self.client.deployments.list(_include=['id'])]
        deployments = {d_id: {'node_instances': [],
                              'executions': []}
                       for d_id in deployment_ids}
        node_instances = self.client.node_instances.list()
        executions = self.client.executions.list()

        for node_instance in node_instances:
            deployment = deployments[node_instance.deployment_id]
            deployment['node_instances'].append(node_instance)
        for execution in executions:
            deployment = deployments[execution.deployment_id]
            deployment['executions'].append(execution)

        return {'deployments': deployments}

    @staticmethod
    def static(filename):
        return bottle.static_file(filename,
                                  root=os.path.join(resources.DIR, 'overview'))

    def index(self):
        return self.static('index.html')

    def serve(self):
        routes = {
            '/': self.index,
            '/metadata': self.metadata,
            '/state': self.state,
            '/static/<filename:path>': self.static,
        }
        for route, handler in routes.items():
            self.app.route(route)(handler)
        self.app.run()


def serve(configuration):
    Overview(configuration).serve()
