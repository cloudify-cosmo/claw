Tips
====

Running System Tests
--------------------
``claw generate`` and ``claw bootstrap`` create a symlink to the last generated
configuration directory in ``$CLAW_HOME/configurations/_``.

With this in place, instead of exporting the ``HANDLER_CONFIGURATION``
environment variable every time you run a system test, to some other
``handler-configuration.yaml`` file, you can export this hard coded environment
variable:

.. code-block:: sh

    export HANDLER_CONFIGURATION=PATH_TO_CLAW_HOME/configurations/_/handler-configuration.yaml

Remember that ``claw bootstrap`` will update ``handler-configuration.yaml``
with the ``manager_ip`` of the newly bootstrapped manager.


Current Configuration
---------------------
As mentioned in the previous section, the last generated/bootstrapped
configuration will always be symlinked at ``$CLAW_HOME/configurations/_``.

As such, you can save some more typing by using ``_`` instead of the
configuration name, in all commands that take the configuration name as their
first argument.

For example, if we recently bootstrapped an environment based on a handler
configuration named ``datacentred_openstack``, and we wish to run some script
with the ``datacentred_openstack`` environment as the script's ``cosmo``,

instead of writing:

.. code-block:: sh

    $ claw script datacentred_openstack my_script

we can instead write:

.. code-block:: sh

    $ claw script _ my_script

to get the same result. Much shorter.

Shell Configuration Navigation
------------------------------
To simplify the process of navigating between configurations,
``claw cdconfiguration`` can be used to generate a bash script that does some
nice things.

First, it adds a function named ``cdconfiguration`` that is basically
implemented like this:

.. code-block:: sh

    cdconfiguration()
    {
        cd PATH_TO_CLAW_HOME/configurations/$1
    }

Not very useful on its own but very useful with the second thing it does which
is to register bash completion for the ``cdconfiguration`` function.

Assuming you have 3 configurations currently generated, named: ``datacentred``,
``hp`` and ``internal``, you can type ``cdconfiguration``, type ``d``, hit tab
and have ``datacentred`` completed. Hit enter, and you're there. easy peasy.

Installation
^^^^^^^^^^^^

To use it, run ``claw cdconfiguration`` and put the output of this command
somewhere in your ``~/.bashrc``.

.. attention::
    Don't put anything like this in your ``~/.bashrc``:

    .. code-block:: sh

        eval "$(claw cdconfiguration)"

    As the ``claw`` command initialization time is very noticeable and this
    will likely cause new shells to start super slowly.
