from abc import ABC, abstractmethod, abstractproperty
from sys import stdout
from typing import IO

from boto3.session import Session

from smokestack.abc.change_set import ChangeSetABC


class StackABC(ABC):
    def __init__(self, writer: IO[str] = stdout) -> None:
        self.session = Session(region_name=self.region)
        self.writer = writer

    @abstractmethod
    def create_change_set(self) -> ChangeSetABC:
        pass

    @abstractproperty
    def region(self) -> str:
        """Gets the AWS region to deploy into."""
