CLI
===

Introduction
------------

**Smokestack** makes your project executable on the command line to easily preview and deploy stacks.

To prepare your project for command line execution:

1. Call :py:func:`smokestack.register` to make your stack sets available.
2. Call :py:func:`smokestack.SmokestackCli.invoke_and_exit` to hand off execution to Smokestack.

Example
-------

In this example, in ``__main__.py__``:

1. :py:func:`smokestack.register` is called three times to make three stack sets available
2. :py:func:`smokestack.SmokestackCli.invoke_and_exit` is called to hand off execution to Smokestack

.. code-block:: python

   from smokestack import register, SmokestackCli

   import myproject.stack_sets


   def cli_entry() -> None:
      register("app", myproject.stack_sets.ApplicationStackSet)
      register("boot", myproject.stack_sets.BootstrapStackSet)
      register("ci", myproject.stack_sets.ContinuousIntegrationStackSet)
      SmokestackCli.invoke_and_exit()


   if __name__ == "__main__":
      cli_entry()

CLI usage
---------

To preview the changes that a stack set *would* deploy, pass the stack set key and ``--preview`` arguments:

.. code-block:: console

   python -m myproject app --preview


To deploy stacks, pass the stack set key and ``--execute`` arguments:

.. code-block:: console

   python -m myproject app --execute

``--execute`` and ``--preview`` can both be passed to generated a detailed log of the changes that a deployment performed:

.. code-block:: console

   python -m myproject app --preview --execute

Functions
---------

.. autofunction:: smokestack.register

.. py:function:: smokestack.SmokestackCli.invoke_and_exit

   Hands execution over to Smokestack. Any command line arguments will be interpreted,
   operated on, then the script will terminate with an appropriate exit code.
