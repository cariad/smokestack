Register Stack Sets in the CLI
==============================

Before your stack sets can be previewed or deployed, they must be registered in the command line interface.

In your project's ``__main__.py``:

1. Call :py:func:`smokestack.register` to make your stack sets available.
2. Call :py:func:`smokestack.SmokestackCli.invoke_and_exit` to hand off execution to Smokestack.

Example
-------

This ``__main__.py`` registers three stack sets then hands off execution to Smokestack:

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

Functions
---------

.. autofunction:: smokestack.register

.. py:function:: smokestack.SmokestackCli.invoke_and_exit

   Hands execution over to Smokestack. Any command line arguments will be interpreted,
   operated on, then the script will terminate with an appropriate exit code.
