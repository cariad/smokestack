from abc import abstractproperty
from pathlib import Path
from sys import stdout
from typing import IO, Union

from smokestack.abc import StackABC
from smokestack.change_set import ChangeSet
from smokestack.types import Capabilities, ChangeType


class Stack(StackABC):
    def __init__(self, writer: IO[str] = stdout) -> None:
        super().__init__(writer=writer)

        self.client = self.session.client(
            "cloudformation",
        )  # pyright: reportUnknownMemberType=false

    @abstractproperty
    def body(self) -> Union[str, Path]:
        """Gets the template body or path to the template file."""

    @property
    def capabilities(self) -> Capabilities:
        return []

    @property
    def change_type(self) -> ChangeType:
        return "UPDATE" if self.exists else "CREATE"

    def create_change_set(self) -> ChangeSet:
        if isinstance(self.body, Path):
            with open(self.body, "r") as f:
                body = f.read()
        else:
            body = self.body

        return ChangeSet(
            capabilities=self.capabilities,
            body=body,
            change_type=self.change_type,
            session=self.session,
            stack=self.name,
            writer=self.writer,
        )

    @property
    def exists(self) -> bool:
        try:
            self.client.describe_stacks(StackName=self.name)
            return True
        except self.client.exceptions.ClientError:
            return False

    @abstractproperty
    def name(self) -> str:
        """Gets the stack name."""
