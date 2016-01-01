Claw - Cloudify Almighty Wrapper
================================

* ``claw`` can help you take the pain out of bootstrapping woes (some of them at least).
* Along the way, ``claw`` can help you with other Cloudify development related
  aspects.
* ``claw`` uses concepts derived from the system tests framework. Mainly,
  handler configurations which are used to describe different environments
  in which you may bootstrap on. It tries doing it in a way that will allow
  you to have many different configurations with as little repetition as
  possible.
* ``claw`` was initially conceived to ease the day to day Cloudify development
  pains of a single developer. It hopes it can do the same for more than one
  developer.
* Using ``claw``, bootstrapping a Cloudify manager looks like this:

  .. code-block:: sh

      $ claw bootstrap openstack_datacentred1


To get started, follow the :doc:`installation` page. Next, don't miss out on
:doc:`bash_completion`. Without it, working with ``claw`` becomes somewhat
inconvenient. Next, read :doc:`bootstrap_and_teardown`.

The other sections are great too, but you can certainly get going without them
in the beginning.


.. toctree::
    :maxdepth: 2

    installation
    bash_completion
    bootstrap_and_teardown
    deploy_and_undeploy
    cleanup
    generate_files
    scripts
