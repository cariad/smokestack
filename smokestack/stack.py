from abc import abstractmethod
from pathlib import Path
from typing import List, Type, Union

from cfp import StackParameters

from smokestack.types import Capabilities


class Stack:
    """
    An Amazon Web Services CloudFormation stack.
    """

    @property
    @abstractmethod
    def body(self) -> Union[str, Path]:
        """
        Gets the template body or path to the template file.
        """

    @property
    def capabilities(self) -> Capabilities:
        """
        Gets the capabilities required to deploy this stack.
        """

        return []

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Gets the stack's name.
        """

    @property
    def needs(self) -> List[Type["Stack"]]:
        """
        Gets the stacks that must be deployed before this one.
        """

        return []

    def parameters(self, params: StackParameters) -> None:
        """
        Populates this stack's parameters.

        Arguments:
            params: Stack parameters. Provided by CFP: https://cariad.github.io/cfp/
        """

        return None

    @property
    @abstractmethod
    def region(self) -> str:
        """
        Gets the Amazon Web Services region to deploy this stack into.
        """
