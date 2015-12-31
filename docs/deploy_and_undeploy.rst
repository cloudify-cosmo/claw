Deploy and Undeploy
===================
The main use case for using ``claw`` in the first place is to bootstrap
Cloudify management environments as painlessly as possible. But, once we have
that in place, why not leverage all this context we have.

One aspect in which this takes place is to allow easy, repeatable deployment
- which means blueprint upload, deployment creation and install workflow
execution; and undeployment - which means uninstall workflow execution,
deployment deletion and blueprint deletion.

Similarly to the bootstrap process, on first look, it would appear doing this
doesn't require any additional tool. ``cfy`` already has everything in place:

.. code-block:: sh

    $ cfy blueprints upload -p /path/to/blueprint.yaml -b my_blueprint
    $ cfy deployments create -b my_blueprint -i /path/to/inputs.yaml
    $ cfy executions start -w install

While this document is written, ``cfy install`` is not integrated into ``cfy``
yet, but with it, this process should be even simpler.

So, how can ``claw`` simplify this process?

The answer lies on a configuration mechanism that if very similar in nature
to the handler configuration mechanism that has been described in
:doc:`bootstrap_and_teardown`.

Configurations
--------------
During ``claw init``, in addition to the generated ``suites.yaml`` file,
a file named ``blueprints.yaml`` was also generated. The structure of this file
is similar to that of ``suites.yaml`` but much simpler.

It has two sections: ``variables``, which should be familiar to you from
``suites.yaml`` and ``blueprints``, which logically, serves the same purpose of
``handler_configurations`` in ``suites.yaml``.

Deploy and Blueprint Configurations
-----------------------------------

In the following examples, we shall assume that a Cloudify management
environment was bootstrapped based on a configuration named
``datacentred_openstack``.

Simplest Example
^^^^^^^^^^^^^^^^
For this section we'll use the following basic ``blueprints.yaml``:

.. code-block:: yaml

    blueprints:
      openstack_nodecellar:
        blueprint: ~/dev/cloudify/cloudify-nodecellar-example/openstack-blueprint.yaml
        inputs: /path/to/nodecellar/openstack/inputs.yaml

With this blueprint configuration in place, you can run (from any directory):

.. code-block:: sh

    $ claw deploy datacentred_openstack openstack_nodecellar

To deploy (upload blueprint, create deployment and execute install workflow)
nodecellar on the ``datacentred_openstack`` environment.

The command above created a directory at
``$CLAW_HOME/configurations/datacentred_openstack/blueprints/openstack_nodecellar``.

This directory contains:

* A copy of the ``inputs.yaml`` supplied.
* A directory named ``blueprint`` which is a copy of the original
  blueprint directory (with the exception that the blueprint file was
  renamed to ``blueprint.yaml``, if named differently)
* A ``blueprint-configuration.yaml`` file that, at the moment, is not very
  useful and has the supplied ``inputs`` and ``blueprint`` fields in it.

Inputs and Blueprint Override
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Now, we'll build upon the previous example, making use of ``inputs_override``:

.. code-block:: yaml

  openstack_nodecellar:
    blueprint: ~/dev/cloudify/cloudify-nodecellar-example/openstack-blueprint.yaml
    inputs: ~/dev/cloudify/cloudify-nodecellar-example/inputs/openstack.yaml.template
    inputs_override:
      image: MY_IMAGE_ID
      flavor: MY_FLAVOR
      agent_user: AGENT_USERNAME

The previous blueprint configuration uses a the default openstack nodecellar
blueprint and the inputs template file that comes with. In addition, it uses
``inputs_override`` to override the ``image``, ``flavor`` and ``agent_user``
inputs.

Similar to the previous section, running:

.. code-block:: sh

    $ claw deploy datacentred_openstack openstack_nodecellar

will deploy nodecellar on the ``datacentred_openstack`` environment.

Note that the generated ``inputs.yaml`` file is not just a
copy of the original inputs file, but rather a merge of its content, overridden
by items specified in ``inputs_override``.

.. note::
    ``blueprint_override`` was not used in the previous example, but has the
    same semantics as those described for ``manager_blueprint_override`` in
    :doc:`bootstrap_and_teardown`.

Variables
^^^^^^^^^
pass

Undeploy
--------
pass