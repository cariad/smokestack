from abc import ABC, abstractmethod
from typing import Any, Optional


class ChangeSetABC(ABC):
    @abstractmethod
    def __enter__(self) -> "ChangeSetABC":
        pass

    @abstractmethod
    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        pass

    @abstractmethod
    def preview(self, options: Optional[Any] = None) -> None:
        pass

    @abstractmethod
    def execute(self) -> None:
        pass
