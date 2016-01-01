Generate Files
==============
There may be times when you don't want ``claw`` to do the actual bootstrap or
deployment process for you, but you do want it to generate the initial files
for you.

Maybe because the system test you are working on performs the bootstrap.
Maybe you need to make some complex modifications that are not catered by the
override mechanism. Maybe you just like having more control on the process.

For whatever reason it may be, ``claw`` comes with two commands that will
generate manager and regular blueprints for you. These commands are
``claw generate`` and ``claw generate-blueprint``.

.. note::
    Under the hood, when you run ``claw bootstrap`` and ``claw deploy``,
    ``claw`` uses the same ``generate``, and ``generate-blueprint`` commands.


Generate Manager Blueprints
---------------------------

To generate a manager blueprint based on a handler configuration, run:

.. code-block:: sh

    $ claw generate CONFIGURATION_NAME

The previous command will generate all the files in a directory located at
``$CLAW_HOME/configurations/CONFIGURATION_NAME`` as described in
:doc:`bootstrap_and_teardown`.

``claw generate`` accepts the same flags as ``claw bootstrap``. These are
described in :doc:`bootstrap_and_teardown`.

Generate Blueprints
-------------------

To generate a blueprint based on a blueprint configuration, within a handler
configuration based environment, run:

.. code-block:: sh

    $ claw generate-blueprint CONFIGURATION_NAME BLUEPRINT_NAME

The previous command will generate all the files in a directory located at
``$CLAW_HOME/configurations/CONFIGURATION_NAME/blueprints/BLUEPRINT_NAME`` as
described in :doc:`deploy_and_undeploy`.

Reset Configuration
-------------------
All commands accept a ``--reset`` flag that will remove the current
configuration directory. Use with care.
