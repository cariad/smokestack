from dataclasses import dataclass
from io import StringIO
from typing import Optional


@dataclass
class OperationResult:
    out: StringIO
    token: str
    exception: Optional[str] = None
