from abc import ABC, abstractproperty
from pathlib import Path
from sys import stdout
from typing import IO, Union

from boto3.session import Session

from smokestack.change_set import ChangeSet
from smokestack.types import Capabilities, ChangeType


class Stack(ABC):
    def __init__(self, session: Session, writer: IO[str] = stdout) -> None:
        self.client = session.client(
            "cloudformation",
            region_name=self.region,
        )  # pyright: reportUnknownMemberType=false
        self.session = session
        self.writer = writer

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
            region=self.region,
            session=self.session,
            stack_name=self.name,
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

    @abstractproperty
    def region(self) -> str:
        """Gets the AWS region to deploy into."""
