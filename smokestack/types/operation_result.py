from dataclasses import dataclass
from typing import Optional, Type

from smokestack.protocols import StackProtocol
from smokestack.types.operation import Operation


@dataclass
class OperationResult:
    operation: Operation
    stack: Type[StackProtocol]
    exception: Optional[str] = None
