import jinja2
import bottle

from systest_manager import resources


class Overview(object):

    def __init__(self, configuration):
        self.app = bottle.app()
        self.configuration = configuration
        self.client = configuration.client
        self.host = self.client._client.host

    def _content(self, deployment_ids):
        deployments = {d_id: {'node_instances': {},
                              'executions': {}}
                       for d_id in deployment_ids}
        deployment_id = deployment_ids[0] if len(deployment_ids) == 1 else None
        node_instances = self.client.node_instances.list(
            deployment_id=deployment_id)
        executions = self.client.executions.list(deployment_id=deployment_id)

        for node_instance in node_instances:
            deployment = deployments[node_instance.deployment_id]
            deployment['node_instances'][node_instance.id] = node_instance
        for execution in executions:
            deployment = deployments[execution.deployment_id]
            deployment['executions'][execution.id] = execution

        template = jinja2.Template(resources.get('overview.html'))
        return template.render(
            version=self.client.manager.get_version()['version'],
            host=self.host,
            configuration=self.configuration.configuration,
            deployments=deployments)

    def all_deployments(self):
        return self._content([d.id for d in
                              self.client.deployments.list(_include=['id'])])

    def single_deployment(self, deployment_id):
        return self._content([deployment_id])

    def serve(self):
        routes = {
            '/': self.all_deployments,
            '/<deployment_id>': self.single_deployment
        }
        for route, handler in routes.items():
            self.app.route(route)(handler)
        self.app.run()


def serve(configuration):
    Overview(configuration).serve()
