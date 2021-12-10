# from io import StringIO
from pathlib import Path
from typing import Protocol, Union

from boto3.session import Session
from cfp import StackParameters

from smokestack.types.capability import Capabilities


class StackProtocol(Protocol):
    @property
    def body(self) -> Union[str, Path]:
        """
        Gets the template body or path to the template file.
        """
        ...

    @property
    def capabilities(self) -> Capabilities:
        """Gets the capabilities required to deploy this stack."""

        ...

    @property
    def exists(self) -> bool:
        """Returns `True` if the stack exists, otherwise `False`."""
        ...

    @property
    def name(self) -> str:
        """Gets the stack's name."""
        ...

    def parameters(self, params: StackParameters) -> None:
        """
        Gets stack parameters
        """
        ...

    @property
    def session(self) -> Session:
        """Gets this stack's Boto3 session."""
        ...

    @property
    def stack_parameters(self) -> StackParameters:
        ...
