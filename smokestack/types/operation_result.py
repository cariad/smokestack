from dataclasses import dataclass
from io import StringIO
from typing import Optional, Type

from smokestack.protocols import StackProtocol
from smokestack.types.operation import Operation


@dataclass
class OperationResult:
    operation: Operation
    out: StringIO
    stack: Type[StackProtocol]
    exception: Optional[str] = None
