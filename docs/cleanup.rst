Cleanup
=======

``claw`` exposes two different cleanup mechanisms. One mechanism is used to
``undeploy`` **all** deployments on a Cloudify manager, the other mechanism is
used to remove **all** IaaS resources in an environment.

Deployment Cleanup
------------------
To undeploy **all** deployments on a ``claw`` based Cloudify manager
environment, run:

.. code-block:: sh

    $ claw cleanup-deployments CONFIGURATION_NAME

This command will iterate all deployments on the Cloudify manager and for each
deployment the ``uninstall`` workflow will be executed, the deployment will be
deleted and its blueprint will be deleted.

To cancel currently running executions of deployments before the undeployment
process, pass the ``--cancel-executions`` to the ``claw cleanup-deployments``
command.

.. warning::
    Internally, ``claw cleanup-deployments`` will pass ``--ignore-live-nodes``
    to the underlying ``cfy deployments delete`` commands.
    You should be aware of this when using this command.


IaaS Cleanup
------------
To remove **all** IaaS resources on the IaaS used by a certain configuration,
run:

.. code-block:: sh

    $ claw cleanup CONFIGURATION_NAME

.. note::
    At the moment, the ``claw cleanup`` command is only implemented for
    openstack based environments.

.. note::
    On openstack, ``claw cleanup`` will not delete key pairs by default.
    To make the ``claw cleanup`` command delete key pairs, add
    ``delete_keypairs: true`` to the relevant handler configuration.
    For example:

    .. code-block:: yaml

        handler_configurations:
          some_openstack_env:
            ...
            delete_keypairs: true
