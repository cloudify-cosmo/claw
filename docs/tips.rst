Tips
====

Running System Tests
--------------------
``claw generate`` and ``claw bootstrap`` create a symlink to the last generated
configuration directory in ``$CLAW_HOME/configurations/+``.

With this in place, instead of exporting the ``HANDLER_CONFIGURATION``
environment variable every time you run a system test, to some other
``handler-configuration.yaml`` file, you can export this hard coded environment
variable:

.. code-block:: sh

    export HANDLER_CONFIGURATION=PATH_TO_CLAW_HOME/configurations/+/handler-configuration.yaml

Remember that ``claw bootstrap`` will update ``handler-configuration.yaml``
with the ``manager_ip`` of the newly bootstrapped manager.


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
