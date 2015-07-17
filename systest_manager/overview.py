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

    def events(self, execution_id):
        node_id = bottle.request.query.get('node_id')
        events, _ = self.client.events.get(
            execution_id=execution_id,
            batch_size=1000,
            include_logs=True)
        if node_id:
            events = [e for e in events
                      if e['context'].get('node_id') == node_id]
        for event in events:
            event['type'] = ('LOG' if 'cloudify_log' in event['type']
                             else 'CFY')

        return {'events': events}

    @staticmethod
    def static(filename):
        return bottle.static_file(filename,
                                  root=os.path.join(resources.DIR, 'overview'))

    def index(self):
        return self.static('index.html')

    def serve(self, port):
        routes = {
            '/': self.index,
            '/metadata': self.metadata,
            '/state': self.state,
            '/events/<execution_id>': self.events,
            '/static/<filename:path>': self.static,
        }
        for route, handler in routes.items():
            self.app.route(route)(handler)
        print 'http://localhost:{0}'.format(port)
        self.app.run(debug=True, port=port)


def serve(configuration, port):
    Overview(configuration).serve(port=port)
