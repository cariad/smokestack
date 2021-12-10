from abc import abstractmethod
from pathlib import Path
from typing import List, Type, Union

from cfp import StackParameters

from smokestack.types import Capabilities


class Stack:
    """
    An Amazon Web Services CloudFormation stack.

    The following members must be implemented:

    - (property) body

    The following members can be implemented as-needed:

    - (property) capabilities

    """

    @property
    @abstractmethod
    def body(self) -> Union[str, Path]:
        """Gets the template body or path to the template file."""

    @property
    def capabilities(self) -> Capabilities:
        """Gets the capabilities required to deploy this stack."""
        return []

    @property
    @abstractmethod
    def name(self) -> str:
        """Gets the stack's name."""

    @property
    def needs(self) -> List[Type["Stack"]]:
        """
        Gets the stacks that must be deployed before this one.

        The stack has no dependencies by default. Override this property only if
        you have dependencies to describe.

        In this example, Smokestack will ensure that the database and logging
        stacks are deployed before deploying the application stack:

        .. code-block:: python

            from smokestack import Stack

            import myproject.stacks


            class ApplicationStack(Stack):

                # ...

                @property
                def needs(self) -> List[Type[Stack]]:
                    return [
                        myproject.stacks.DatabaseStack,
                        myproject.stacks.LoggingStack,
                    ]
        """

        return []

    def parameters(self, params: StackParameters) -> None:
        """
        Populates this stack's parameters.

        Arguments:
            params: Stack parameters. Call `add()` to add parameters and values.
        """

        return None

    @property
    @abstractmethod
    def region(self) -> str:
        """Gets the Amazon Web Services region to deploy this stack into."""
