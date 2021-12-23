Stacks
======

A *stack* in Smokestack literally represents a CloudFormation stack.

Your project will contain a :py:class:`smokestack.Stack` class for each stack to be deployed.

Describing a minimal stack
--------------------------

At the very least, your stack class must implement:

- :py:attr:`smokestack.Stack.body`: Return either the body of the template as a string or a ``pathlib.Path`` that describes the location of a template file.
- :py:attr:`smokestack.Stack.name`: Return the name of the stack.
- :py:attr:`smokestack.Stack.region`: Return the Amazon Web Services region to deploy into.

.. code-block:: python

    from pathlib import Path

    from smokestack import Stack


    class ApplicationStack(Stack):
        @property
        def body(self) -> Path:
            return Path("templates") / "app.cf.yml"

        @property
        def name(self) -> str:
            return "Application"

        @property
        def region(self) -> str:
            return "us-east-1"

Capabilities
------------

To describe any capabilities that your stack requires, override :py:attr:`smokestack.Stack.capabilities` to return a string list.

.. code-block:: python

    from smokestack import Capabilities, Stack


    class ApplicationStack(Stack):
        @property
        def capabilities(self) -> Capabilities:
            return [
                "CAPABILITY_IAM",
            ]

Dependencies
------------

To describe any upstream stacks that must be deployed before this one, override :py:attr:`smokestack.Stack.needs` to return the other stack types.

.. code-block:: python

    from smokestack import Capabilities, Stack

    import myproject.stacks


    class ApplicationStack(Stack):
        @property
        def needs(self) -> : List[Type[Stack]]:
            return [
                myproject.stacks.DatabaseStack,
                myproject.stacks.LoggingStack,
            ]

Parameters
----------

To describe any parameter values that your stack requires, override the :py:func:`smokestack.Stack.parameters` function. This will provide a `CFP <https://cariad.github.io/cfp>`_ ``StackParameters`` instance to add parameter values to.

.. code-block:: python

    from cfp import StackParameters
    from smokestack import Capabilities, Stack


    class ApplicationStack(Stack):
        def parameters(self, params: StackParameters) -> None:
            params.add("InstanceType", "t3.large")


See the `CFP <https://cariad.github.io/cfp>`_ documentation for ``StackParameters``  tips and tricks.

Post-execution actions
----------------------

To perform some post-execution action (e.g. to copy files into an S3 bucket that your stack deployed) override the :py:func:`smokestack.Stack.post` function.

``Stack`` class
---------------

.. autoclass:: smokestack.Stack
   :members:
