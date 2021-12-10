from pathlib import Path
from typing import Protocol, Union

from cfp import StackParameters

from smokestack.types.capability import Capabilities


class StackProtocol(Protocol):
    @property
    def body(self) -> Union[str, Path]:
        """Gets the template body or path to the template file."""
        ...

    @property
    def capabilities(self) -> Capabilities:
        """Gets the capabilities required to deploy this stack."""
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
    def region(self) -> str:
        """Gets the Amazon Web Services region to deploy this stack into."""
        ...
