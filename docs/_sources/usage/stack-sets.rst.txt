Stack Sets
==========

A *stack set* is a collection of one or more stacks to be previewed or deployed.

Your project will contain a :py:class:`smokestack.StackSet` class for each stack set to be deployed.

Describing a stack set
----------------------

Implement the :py:attr:`smokestack.StackSet.stacks` property to return the stacks within this set.

For example, this "Platform" stack set describes application, database and logging stacks:

.. code-block:: python

    from smokestack import Stack, StackSet

    import myproject.stacks


    class PlatformStackSet(StackSet):
        @property
        def stacks(self) -> List[Type[Stack]]:
            return [
                myproject.stacks.ApplicationStack,
                myproject.stacks.DatabaseStack,
                myproject.stacks.LoggingStack,
            ]

``StackSet`` class
------------------

.. autoclass:: smokestack.StackSet
   :members:
