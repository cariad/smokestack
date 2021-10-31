from abc import ABC, abstractmethod
from sys import stdout
from typing import IO

from boto3.session import Session

from smokestack.abc.change_set import ChangeSetABC


class StackABC(ABC):
    def __init__(self, session: Session, writer: IO[str] = stdout) -> None:
        self.session = session
        self.writer = writer

    @abstractmethod
    def create_change_set(self) -> ChangeSetABC:
        pass
