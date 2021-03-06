Installation
============

Prerequisites
-------------
`cloudify-system-tests <https://github.com/cloudify-cosmo/cloudify-system-tests>`_
should be installed in editable mode in the relevant virtualenv.

Installing The Code
-------------------

.. code-block:: sh

    $ pip install https://github.com/dankilman/claw/archive/master.tar.gz

.. note::
    ``claw`` is updated quite frequently at the moment, so you may want to
    consider cloning the ``claw`` repo, and installing it in editable mode.
    This way, updates will be as easy as ``git pull`` in the repo local
    directory.

Setting Up The Environment
--------------------------
#. Choose a location that will serve as the base directory for all ``claw``
   related configuration and generated files. For example:

    .. code-block:: sh

        $ export CLAW_HOME=$HOME/claw
        $ mkdir -p $CLAW_HOME

#. Initialize ``claw`` in the base directory. While we run ``init`` in a
   specific directory, note that initialization is only performed once,
   i.e. the init configuration will be stored in ``~/.claw`` and subsequent
   ``claw`` commands can be executed from any directory, not specifically the
   directory in which ``init`` was performed.

    .. code-block:: sh

        $ cd $CLAW_HOME
        $ claw init

The ``init`` command created two files: ``suites.yaml`` and ``blueprints.yaml``
which are covered in their own sections. It also created a directory named
``configurations`` which is where generated manager blueprint configurations
will be placed and a directory named ``scripts`` prepopulated with an example
script.

It will make sense to have the base directory managed by some version control
system (i.e. ``git``, privately, as these configuration files will probably
contain credentials, etc...)

The next sections go into details showing how ``claw`` may be useful in
simplifying your day to day interactions with Cloudify.
