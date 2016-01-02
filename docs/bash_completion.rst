Bash Completion
===============
Working with ``claw`` can get quite verbose at times due to long descriptive
configuration and blueprint names and many options that may be passed as
arguments.

This is why properly configuring your bash environment to autocomplete ``claw``
commands is highly recommended. Really, **highly** recommended, don't skip
this part even if you're feeling lazy.

Virtualenvwrapper
-----------------
If you use ``virtualenvwrapper``, a clean solution to have autocomplete only
available when running inside the Cloudify related virtualenv, would be to add
it to the virtualenv ``postactivate`` script, like this:

.. code-block:: sh

    $ workon VIRTUALENV_NAME
    $ cdvirtualenv
    $ ${EDITOR} bin/postactivate

Next, add the following to the ``postactivate`` script:

.. code-block:: sh

    eval "$(register-python-argcomplete claw)"

Plain Bash
----------
If you don't use ``virtualenvwrapper``, consider using it. It's
great.

If you're still not persuaded, put something like this in your ``~/.bashrc``:

.. code-block:: sh

    if command -v register-python-argcomplete > /dev/null 2>&1; then
        eval "$(register-python-argcomplete claw)"
    fi


Verify It Works
---------------
Open a new shell, ``activate`` or ``workon`` your virtualenv, type ``claw``,
hit tab twice (three times if you typed ``claw`` with no space) and you should
be seeing something like this:

.. code-block:: sh

    $ claw <TAB> <TAB>
    --help               cdconfiguration      deploy               generate-script      status
    -h                   cleanup              generate             init                 teardown
    bootstrap            cleanup-deployments  generate-blueprint   script               undeploy
