======================
Bootstrap and Teardown
======================

The main reason ``claw`` was written in the first place, was to simplify the
process of bootstrapping during development.

You may have many environments in which you bootstrap on, ``aws`` based environments,
``openstack`` based environments, etc...
Each environments has its own set of ``inputs``, such as different credentials,
different resource names, etc...
At the same time, some set of properties may be shared between environments
which means duplication. You get the drift.

Similar modifications may be required in the different manager blueprints,
which suffer from the same problems.

At the same time, during development, you generally want to use the tip of the
``master`` or build branch of the ``cloudify-manager-blueprints`` repository.

All these different constraints, will likely cause you many headaches, sporadic
failures due to some manual typing gone wrong and similar mishaps.

``claw`` can help you keep you sanity.

Configurations
--------------
Before we delve into how you would actually bootstrap using ``claw``, we need
to discuss the concept of configurations.

When ``CLAW_HOME`` was initialized during ``claw init``, a file named
``suites.yaml`` was generated in it. The name ``suites.yaml`` may be familiar
to you from ``cloudify-system-tests``, this is not coincidental.

``claw`` leverages the concept of ``handler_configurations`` used by the system
tests framework to configure different environments. If you are not familiar
with the system tests ``suites.yaml``, that's OK, this guide will try not
making the assumption of familiarity.

The sections in ``suites.yaml`` are:

* ``handler_configurations``
* ``variables``
* ``manager_blueprint_override_templates``
* ``inputs_override_templates``
* ``handler_configuration_templates``

For now, we'll focus on the ``handler_configurations`` sections, and ignore the
others.

Bootstrap and Handler Configurations
------------------------------------

Simplest example
^^^^^^^^^^^^^^^^

For this section we'll use the following basic ``suites.yaml``:

.. code-block:: yaml

    handler_configurations:
      some_openstack_env:
        manager_blueprint: /path/to/my-manager-blueprint.yaml
        inputs: /path/to/my-manager-blueprint-inputs.yaml

With this configuration in place, you can run (from any directory):

.. code-block:: sh

    $ claw bootstrap some_openstack_env

To bootstrap a manager.

The command above created a directory at
``$CLAW_HOME/configurations/some_openstack_env``.

This directory contains:

* A copy of the ``inputs.yaml`` supplied.
* A directory named ``manager-blueprint`` which is a copy of the original
  manager blueprint directory (with the exception that the blueprint file was
  renamed to ``manager-blueprint.yaml``)
* A ``handler_configuration.yaml`` file that can be used to run system tests on
  the manager that was just bootstrapped.

In addition, ``cfy init`` and ``cfy bootstrap`` were executed in this directory
by ``claw`` and ``.cloudify/config.yaml`` was configured so that you can see
colors when running bootstrap/teardown and other workflows, which is nice.

Of course, this is not very useful and can be easily achieve directly from
``cfy``:

.. code-block:: sh

    $ cfy init
    $ cfy bootstrap -p /path/to/my-manager-blueprint.yaml -i /path/to/my-manager-blueprint-inputs.yaml

And while this did not do all these things that ``claw`` did previously, in
most cases, this may be enough. So let's take it up a notch and start using
more advanced ``handler_configuration`` features.

Inputs and Manager Blueprint Override
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now, we'll build upon the previous example, making use of ``inputs_override``
and ``manager_blueprint_override``:

.. code-block:: yaml

    handler_configurations:
      some_openstack_env:
        manager_blueprint: /path/to/my-needs-a-patch-manager-blueprint.yaml
        inputs: /path/to/my-partially-filled-manager-blueprint-inputs.yaml
        inputs_override:
          keystone_username: MY_USERNAME
          keystone_password: MY_PASSWORD
          keystone_tenant_name: MY_TENANT_NAME
        manager_blueprint_override:
          node_templates.management_subnet.properties.subnet.dns_nameservers: [8.8.4.4, 8.8.8.8]

The previous handler configuration uses a manager blueprint that needs some
fix to the management network subnet dns configuration.
In addition an inputs file that has everything filled excpet for the username,
password and tenant name. Of course, it also configures ``inputs_override`` and
``manager_blueprint_override``.

Simliar to the previous section, running:

.. code-block:: sh

    $ claw bootstrap some_openstack_env

will bootstrap the manager.

The new thing here, is that the generated ``inputs.yaml`` file is not just a
copy of the original inputs file, but rather a merge of its content, overriden
by items specified in ``inputs_override``. Similarly, the copy of the manager
blueprint was modified so the the ``management_subnet`` node template, has the
required ``dns_nameservers`` property in place.

Variables
^^^^^^^^^
Variables let you keep values in one places and references them in inputs and
manager blueprint overrides.

We'll modify the previous example and extend it to use variables:

.. code-block:: yaml

    variables:
      username: MY_USERNAME
      password: MY_PASSWORD
      tenant: MY_TENANT_NAME

    handler_configurations:
      some_openstack_env:
        manager_blueprint: /path/to/my-manager-blueprint.yaml
        inputs: /path/to/my-partially-filled-manager-blueprint-inputs.yaml
        inputs_override:
          keystone_username: '{{username}}'
          keystone_password: '{{password}}'
          keystone_tenant_name: '{{tenant}}'

As you can see, variables are pretty straightforward to use. Inside a string,
use ``{{VARIABLE_NAME}}`` to reference a variable. Variables can also be used
as part of a larger string. For example, if we have a variable named ``my_var``
we can use it inside a string like this: ``some_value_{{my_var}}``

In addition to defining your own variables and using them in handler
configurations, you can reference variables that are defined in the
``suites.yaml`` file that is located in the ``cloudify-system-tests``
repository. For example, if the system tests ``suites.yaml`` contains a
variable named ``datacentred_openstack_centos_7_image_id``, you can reference
it just the same, without it being defined in your ``suites.yaml`` file:

.. code-block:: yaml

    handler_configurations:
      some_openstack_env:
        manager_blueprint: /path/to/my-manager-blueprint.yaml
        inputs: /path/to/my-partially-filled-manager-blueprint-inputs.yaml
        inputs_override:
          image_id: '{{datacentred_openstack_centos_7_image_id}}'

Teardown
--------
pass
