Deploy and Undeploy
===================
The main use case for using ``claw`` in the first place is to bootstrap
Cloudify management environments as painlessly as possible. But, once we have
that in place, why not leverage all this context we have.

One aspect in which this takes place, is to allow fast, repeatable deployments
- which means blueprint upload, deployment creation and ``install`` workflow
execution; and undeployment - which means ``uninstall`` workflow execution,
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

The answer lies in a configuration mechanism that is very similar in nature
to the handler configuration mechanism that has been described in
:doc:`bootstrap_and_teardown`.

Configurations
--------------
During ``claw init``, in addition to the generated ``suites.yaml`` file,
a file named ``blueprints.yaml`` is also generated. The structure of this file
is similar to that of ``suites.yaml``.

It has two sections: ``variables``, which should be familiar to you from
``suites.yaml`` and ``blueprints``, which logically, serves the same purpose as
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

To deploy nodecellar on the ``datacentred_openstack`` environment. (upload
blueprint, create deployment and execute ``install`` workflow)

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
Next, we'll build upon the previous example, making use of ``inputs_override``:

.. code-block:: yaml

  openstack_nodecellar:
    blueprint: ~/dev/cloudify/cloudify-nodecellar-example/openstack-blueprint.yaml
    inputs: ~/dev/cloudify/cloudify-nodecellar-example/inputs/openstack.yaml.template
    inputs_override:
      image: MY_IMAGE_ID
      flavor: MY_FLAVOR
      agent_user: AGENT_USERNAME

The previous blueprint configuration uses the default openstack nodecellar
blueprint and the inputs template file that comes with it. In addition, it uses
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
Variables behave in a similar manner to how they behave in ``suites.yaml``
as described in :doc:`bootstrap_and_teardown`.

There are two things to note, though.

First, just as the handler configuration using variables in the user
``suites.yaml`` can reference variables defined in the system tests
``suites.yaml``, blueprint configurations can use variables defined in
the system tests ``suites.yaml``, the user defined ``suites.yaml`` and
variables defined directly in ``blueprints.yaml``.

In addition, the handler configuration ``properties`` are exposed in the
variables used in blueprint configurations. For example, building upon the
previous section:

.. code-block:: yaml

    variables:
      agent_user: ubuntu

    blueprints:

      openstack_nodecellar:
        blueprint: ~/dev/cloudify/cloudify-nodecellar-example/openstack-blueprint.yaml
        inputs: ~/dev/cloudify/cloudify-nodecellar-example/inputs/openstack.yaml.template
        inputs_override:
          image: '{{properties.ubuntu_trusty_image_id}}'
          flavor: '{{properties.small_flavor_id}}'
          agent_user: '{{agent_user}}'


The ``openstack_nodecellar`` blueprint configuration uses the ``agent_user``
variable defined in the same file and ``properties.ubuntu_trusty_image_id``
and ``properties.small_flavor_id`` that come from the properties defined
in the handler configuration. These are the same properties used by system
tests when they use ``self.env.ubuntu_trusty_image_id`` for example.

The nice thing about using properties, is that they will contain correct values
when switching between different environments as opposed to hard coded values
or plain variable references.

Reset Configuration
-------------------
``claw deploy`` accept a ``--reset`` flag that will remove the current
configuration directory. Use with care.

Undeploy
--------
To undeploy (execute ``uninstall`` workflow, delete deployment and delete
blueprint), assuming the blueprint configuration is named
``openstack_nodecellar`` run:

.. code-block:: sh

    $ claw undeploy datacentred_openstack openstack_nodecellar

To cancel currently running executions before starting the undeploy process,
pass the ``--cancel-executions`` flag to the ``claw undeploy`` command.

.. caution::
    Internally, ``claw undeploy`` will pass ``--ignore-live-nodes`` to the
    underlying ``cfy deployments delete`` command to save
    you some typing. You should be aware of this when using this command.
