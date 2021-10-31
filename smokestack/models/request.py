from dataclasses import dataclass
from sys import stdout
from typing import IO, Dict, List, Optional, Type

from smokestack.abc.stack import StackABC
from smokestack.models.host import Host


@dataclass
class Request:
    host: Host
    """Host application."""

    stacks: Dict[str, Type[StackABC]]
    """Deployable stacks."""

    cli_args: Optional[List[str]] = None
    """CLI arguments. Will determinate automatically by default."""

    writer: IO[str] = stdout
    """Output writer. Will use `stdout` by default."""
