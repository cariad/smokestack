CLI Usage
=========

The following examples assume your infrastructure-as-code project is a Python module named ``myproject``.

Preview
-------

To preview the changes that a stack set *would* deploy, pass the stack set key and ``--preview`` arguments:

.. code-block:: console

    python -m myproject app --preview

.. code-block:: text

    🌄 Starting DatabaseStack…
    🌄 Starting LoggingStack…

    🌞 Stack Database in us-east-1

    No changes to apply.

    🌞 Stack Logging in us-east-1

    No changes to apply.

    🌞 Stack Application in us-east-1

    InstanceType = t2.large

    Template changes:
    Description: Application  =  Description: Application
    Parameters:               =  Parameters:
      InstanceType:           =    InstanceType:
        Type: String          =      Type: String
    Resources:                =  Resources:
                              >    ExampleResource:
                              >      Properties:
                              >        InstanceType:
                              >          Ref: InstanceType

    Logical ID       Physical ID    Resource Type           Action
    ExampleResource                 AWS::Example::Resource  Add

    🥳 Done!

Execute
-------

To deploy a stack set's changes, pass the stack set key and ``--execute`` arguments:

.. code-block:: console

    python -m myproject app --preview

.. code-block:: text

    🌄 Starting DatabaseStack…
    🌄 Starting LoggingStack…

    🌞 Stack Database in us-east-1

    No changes to apply.

    🌞 Stack Logging in us-east-1

    No changes to apply.

    🌞 Stack Application in us-east-1

    InstanceType = t2.large

    Executed successfully! 🎉

    🥳 Done!


Note that you can pass both ``--execute`` and ``--preview`` to generated a detailed log of the changes that a deployment performed.

Logging
-------

To emit debug logs, pass ``--log-level debug``.
