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
  the manager that was just bootstrapped. (with ``manager_ip`` properly
  configured)

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

System Tests Fields
^^^^^^^^^^^^^^^^^^^
As mentioned previously, when ``claw bootstrap`` is called, it will generate
a file named ``handler-configuration.yaml`` under
``$CLAW_HOME/configurations/{CONFIGURATION_NAME}`` that is suitable for use
when running system tests locally on the bootstrapped manager.

For this file to be fully suitable, it is up to you, to add the relevant fields
to the handler configuration. These fields are ``properties`` and ``handler``.

The ``properties`` field should be a name that is specified under the
``handler_properties`` section of the system tests ``suites.yaml``.

The ``handler`` field should be a handler that matches the environment on
which the bootstrap is performed.

For example, a handler configuration for running tests on datacentred openstack
might look like this:

.. code-block:: yaml

    handler_configurations:
      some_openstack_env:
        manager_blueprint: /path/to/my-manager-blueprint.yaml
        inputs: /path/to/my-manager-blueprint-inputs.yaml
        handler: openstack_handler
        properties: datacentred_openstack_properties

YAML Anchors (&), Aliases (*) and Merges (<<)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
While not specific to handler configurations, usage of YAML anchors, aliases
and merges can greatly reduce repetition of complex configurations and improve
reusability of different components in the handler configurations.

In the following example, we'll see how YAML anchors, aliases and merges can be
used in handler configurations.

We'll start be giving an example of a somewhat complex annotated
``suites.yaml``, and explain what's going on afterwards.

.. code-block:: yaml

    # Under this section, we put templates that will be used in manager
    # blueprint override sections
    manager_blueprint_override_templates:

      # For now ignore the key 'openstack_dns' and notice the
      # anchor (&) 'openstack_dns_servers_blueprint_override'
      openstack_dns: &openstack_dns_servers_blueprint_override
        node_templates.management_subnet.properties.subnet.dns_nameservers: [8.8.4.4, 8.8.8.8]

      # For now ignore the key 'openstack_influx_port' and notice the
      # anchor (&) 'openstack_openinflux_port_blueprint_override'
      openstack_influx_port: &openstack_openinflux_port_blueprint_override
        # The [append] means that this dict (that contains port and
        # remote_ip_prefix) will be added to the rules list in the overridden
        # manager blueprint
        node_templates.management_security_group.properties.rules[append]:
          port: 8086
          remote_ip_prefix: 0.0.0.0/0

    # Under this section, we put templates that will be used in inputs
    # override sections
    inputs_override_templates:

      # For now ignore the key 'datacentred_openstack_env' and notice the
      # anchor (&) 'datacentred_openstack_env_inputs'
      datacentred_openstack_env: &datacentred_openstack_env_inputs
        keystone_username: MY_USERNAME
        keystone_password: MY_PASSWORD
        keystone_tenant_name: MY_TENTANT_NAME
        keystone_url: MY_KEYSTONE_URL
        external_network_name: MY_EXTERNAL_NETWORK_NAME
        image_id: MY_IMAGE_ID
        flavor_id: MY_FLAVOR_ID
        region: MY_REGION

    # Under this section, we put templates that will be used in handler
    # configurations
    handler_configuration_templates:
      # Notice the anchor (&) 'openstack_handler_configuration'
      # also notice that in this section, templates are specified as list
      # instead of a dict like the previous template sections.
      # It is not required that this section will be a list (i.e. it can be a
      # dict as well), but it is required that the previous sections remain
      # dicts
      - &openstack_handler_configuration
        handler: openstack_handler
        inputs: ~/dev/cloudify/cloudify-manager-blueprints/openstack-manager-blueprint-inputs.yaml
        manager_blueprint: ~/dev/cloudify/cloudify-manager-blueprints/openstack-manager-blueprint.yaml

    handler_configurations:

      # Notice the anchor (&) 'datacentred_handler_configuration'
      datacentred_openstack_env_plain: &datacentred_handler_configuration

        # This is the first place aliases (*) and merges (<<) are used in this
        # file. We merge into the 'datacentred_openstack_env_plain'
        # handler configuration, the content of the handler configuration
        # template whose anchor (&) is 'datacentred_openstack_env_plain'.
        # Note, that while this is the first place aliases are used here, this
        # is simply how to example is built. There is nothing stopping you
        # from using them in the templates sections to reference previously
        # defined templates.
        <<: *openstack_handler_configuration

        # we continue populating the handler configuration with regular values
        properties: datacentred_openstack_properties

        # here we use an alias (*) directly to set the value of
        # 'inputs_override' to be the dict specified by the
        # 'datacentred_openstack_env_inputs' anchor (&)
        inputs_override: *datacentred_openstack_env_inputs

      # Defining a modified datacentred handler configuration
      datacentred_openstack_env_with_modified_dns:

        # Notice that we merge (<<) the previously defined handler
        # configuration anchored (&) by 'datacentred_handler_configuration'
        <<: *datacentred_handler_configuration

        # the only modification we make in this handler configuration is
        # setting 'manager_blueprint_override' to have the value of the
        # manager blueprint template anchored (&) with
        # 'openstack_dns_servers_blueprint_override'
        manager_blueprint_override: *openstack_dns_servers_blueprint_override

      # Defining another modified datacentred handler configuration
      datacentred_openstack_env_with_modified_dns_and_openinflux:

        # Notice that we merge (<<) the previously defined handler
        # configuration anchored (&) by 'datacentred_handler_configuration'
        <<: *datacentred_handler_configuration

        manager_blueprint_override:
          # In this handler configuration, we merge (<<) both templates
          # that were defined the the manager blueprint templates sections
          <<: *openstack_dns_servers_blueprint_override
          <<: *openstack_openinflux_port_blueprint_override


Most of what is going on in the previous example, is inlined within the YAML
as comments, so make sure you read through them to understand how it works.

One thing to mention is that even though it may look verbose, we now have
3 slightly different configurations all located close to each other with very
little duplication. This enables us to bootstrap different (but similar)
configurations as easy as:

.. code-block:: sh

    $ claw bootstrap datacentred_openstack_env_plain

.. code-block:: sh

    $ claw bootstrap datacentred_openstack_env_with_modified_dns

.. code-block:: sh

    $ claw bootstrap datacentred_openstack_env_with_modified_dns_and_openinflux

(Probably not in parallel though, as they all share the same tenant and are
likely to interfere with each other)

Inputs and Manager Blueprint Override as Command Line Arguments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
We can now go back to the previous example, where we (not so smoothly) ignored
the keys in the ``inputs_override_templates`` and
``manager_blueprint_override_templates``.

What if we had many small override snippets in these sections? Obviously, we
can't create a configuration for each combination, as there will be too many
pretty soon and the ``suites.yaml`` file will become a mess to maintain.

For that, ``claw`` accepts ``--inputs-override (-i)`` and
``--manager-blueprint-override (-b)`` as flags to the ``claw bootstrap``
command, where several overrides can be passed in a single ``claw bootstrap``
invocation. The values are the key names in the ``inputs_override_templates``
and ``manager_blueprint_override_templates`` sections.

Building on our previous example, if we only had the
``datacentred_openstack_env_plain`` handler configuration, we could do:

.. code-block:: sh

    $ claw bootstrap datacentred_openstack_env_plain -b openstack_dns -b openstack_influx_port

To override the manager blueprints with overrides from the ``openstack_dns``
and ``openstack_influx_port`` manager blueprint templates.

Similarly, if we had an inputs override template named ``my_dev_branches`` and
we wanted to bootstrap with our dev branches override we could do something
like:

.. code-block:: sh

    $ claw bootstrap datacentred_openstack_env_plain -i my_dev_branches

without having to add a new configuration only for the sake of overriding some
branches.

Overrides Syntax
----------------
Internally, ``claw`` uses and extends the
``cosmo_tester.framework.utils:YamlPatcher`` to implement the overriding logic.

First we'll go over features that are provided by the original ``YamlPatcher``.
Next, we'll show an override feature that only exists in ``claw`` (for now).

For the following examples we'll focus on manager blueprint overrides
because they tend to get nested and require more advanced overrides, but there
is nothing stopping you from applying the same methods to inputs override if
your heart desires.

Path Based Overrides
^^^^^^^^^^^^^^^^^^^^
Overrides are based on the path to the key/value.

Manager blueprint snippet:

.. code-block:: yaml

    node_templates:
      management_vm: ...
      management_subnet: ...
      webui: ...

If we wanted to add a full note template to the previous example we'd have an
override like this:

.. code-block:: yaml

    manager_blueprint_override_templates:
      new_node_in_blueprint: &new_node
        # You would usually have a single override under an override template,
        # but there is nothing stopping you from having multiple overrides
        # under the same template if this is what you need.
        node_templates.my_new_node:
          type: cloudify.nodes.Root
          ...

The resulting YAML will look something like:

.. code-block:: yaml

    node_templates:
      management_vm: ...
      management_subnet: ...
      webui: ...
      my_new_node:
        type: cloudify.nodes.Root
        ...

(after applying the override using one of the methods described in this page)

.. note::
    Overriding (or adding a value) that is not nested is still path based, only
    the path to the overridden key is simply the property name.
    This usually applies to inputs overrides as they are mostly not nested.
    (You can find examples of such of overrides in previous sections on this
    page)

.. note::
    Overriding a nested path that doesn't exist will simply create this path
    for you.

    For example, based on this simple YAML:

    .. code-block:: yaml

        node_templates:
          empty_node: {}

    An override like ``node_template.empty_node.some.nested.path: value``, will
    result in a YAML similar to this:

    .. code-block:: yaml

        node_templates:
          empty_node:
            some:
              nested:
                path: value

.. note::
    If an element in a path contains a dot (``.``), you can escape the dot
    using backslash (``\``).

    For example, if we wanted to add a ``configure`` override to some node
    template lifecycle operation:

    .. code-block:: yaml

        node_templates:
          some_node:
            interfaces:
              cloudify.interfaces.lifecycle:
                create: ...

    We'd have something like:

    .. code-block:: yaml

        manager_blueprint_override_templates:
          configure_lifecycle_operation: &lifecycle_operation
            node_templates.some_node.interfaces.cloudify\.interfaces\.lifecycle.configure:
              implementation: ...
              inputs: ...

    And the resulting YAML will look something like:

    .. code-block:: yaml

        node_templates:
          some_node:
            interfaces:
              cloudify.interfaces.lifecycle:
                create: ...
                configure:
                  implementation: ..
                  inputs: ...

    (after applying the override using one of the methods described in this
    page)

Overriding Values in Lists
^^^^^^^^^^^^^^^^^^^^^^^^^^
To override a value of some list item, you can you the ``[SOME_INDEX]``
directive.

For example, if we had this in a manager blueprint:

    .. code-block:: yaml

        node_templates:
          some_node:
            relationships:
              - type: ...
                target: ...
              - type: some.relationship.type
                target: ...

And we wanted to change the type of the second relationship, we'd have an
override similar to this:

.. code-block:: yaml

    manager_blueprint_override_templates:
      change_rel_type: &rel_type
        # note that indexing is zero-based (i.e. the second element is
        # referenced by index 1)
        node_templates.some_node.relationships[1].type: some.other.relationship.type

The resulting YAML will look something like this:

.. code-block:: yaml

    node_templates:
      some_node:
        relationships:
          - type: ...
            target: ...
          - type: some.other.relationship.type
            target: ...

(after applying the override using one of the methods described in this page)

If, on the other hand, we wanted to add a new relationship, we'd use the
``[append]`` directive:

.. code-block:: yaml

    manager_blueprint_override_templates:
      append_rel: &append_rel
        node_templates.some_node.relationships[append]:
            type: ...
            target: some_new_target_node

The resulting YAML will look something like this:

.. code-block:: yaml

    node_templates:
      some_node:
        relationships:
          - type: ...
            target: ...
          - type: ...
            target: ...
          - type: ...
            target: some_new_target_node

(after applying the override using one of the methods described in this page)

Function Based Overrides (Claw Feature Only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
There may be times when you need to do some advanced override that is not
catered by the existing mechanism.

To enable this, ``claw`` extends the system tests ``YamlPatcher`` with an
ability to specify a function that will accept the current overridden value
as its first argument (or ``None`` if no current value exists) and additional
optional arguments and keyword arguments.

We'll implement a simple override function that add appends exclamation marks
to the current value (we will also make it configurable)

.. code-block:: python

    # lives in some.example.module

    def add_excitement(current_value,
                       excitement_count=3,
                       excitement_char='!'):
        assert isinstance(current_value, basestring)
        return '{0}{1}'.format(current_value,
                               excitement_char * excitement_count)


Example YAML:

.. code-block:: yaml

    node_templates:
      management_vm:
        properties:
          property1: value1
          property2: value2
          property3: value3


To use the function we just created we'll define an override that has this
structure:

.. code-block:: yaml

    func: path.to.func.module:function_name
    # the following two are optional
    args: [1,2,3]
    kwargs: {some_kwarg: value, some_kwarg2: 2}

Let's apply this structure to override values in our example

.. code-block:: yaml

    manager_blueprint_override_templates:
      change_props: &change_props_anchor
        node_templates.management_vm.properties.property1:
          func: some.example.module:add_excitement
        # using the args syntax
        node_templates.management_vm.properties.property2:
          func: some.example.module:add_excitement
          args: [5]
        # using the kwargs syntax
        node_templates.management_vm.properties.property3:
          func: some.example.module:add_excitement
          kwargs: {excitement_count: 2, excitement_char: ?}

The resulting YAML will look something like this:

.. code-block:: yaml

    node_templates:
      management_vm:
        properties:
          property1: value1!!!
          property2: value2!!!!!
          property3: value3??

(after applying the override using one of the methods described in this page)

.. note::
    ``claw`` comes with 2 built-in override functions to filter values from
    lists and dictionaries. They can be found at ``claw.patcher:filter_list``
    and ``claw.patcher:filter_dict``.

Teardown
--------
There is not much to say about tearing down an environment bootstrapped by
``claw``.

If we bootstrapped an environment based on ``my_handler_configuration``, we can
perform teardown like this:

.. code-block:: sh

    $ claw teardown my_handler_configuration

.. warning::
    Internally, ``claw teardown`` will pass ``--force`` and
    ``--ignore-deployments`` to the underlying ``cfy teardown`` command to save
    you some typing. You should be aware of this to avoid unfortunate
    accidental teardowns.
