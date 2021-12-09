Getting Started
===============

Requirements
------------

Smokestack requires Python 3.8 or later.

Installation
------------

.. code-block:: console

   pip install smokestack

Prepare your project
---------------------

1. Describe your stacks.
2. Describe your stack sets.
3. :ref:`Prepare your project for command line execution<CLI>`
4. Run it!

Describing a stack
------------------

A *stack* in Smokestack literally represents a CloudFormation stack.

To describe a stack, create a class that inherits from :py:class:`smokestack.Stack` then populate your stack's details.

A minimal example looks like:

.. code-block:: python

   from smokestack import Stack
   from pathlib import Path

   class ApplicationStack(Stack):

      @property
      def body(self) -> Union[str, Path]:
         return Path("templates") / "app.cf.yml"

      @property
      def name(self) -> str:
         return "Application"

      def parameters(self, params: StackParameters) -> None:
         sp.add("InstanceType", FromParameterStore("/App/InstanceType"))

      @property
      def region(self) -> str:
         return "us-east-1"

Read about the :py:class:`smokestack.Stack` class to learn how to set capabilities, dependent stacks and parameters.

Describing a stack set
----------------------

A *stack set* is a set of one or more stacks to be previewed or deployed.

To describe a stack set, create a class that inherits from :py:class:`smokestack.StackSet` then populate your set's details.
