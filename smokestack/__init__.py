import importlib.resources

from smokestack.cli import SmokestackCli
from smokestack.register import register
from smokestack.stack import Stack
from smokestack.stack_set import StackSet
from smokestack.types import Capabilities, Capability, ChangeType

with importlib.resources.open_text(__package__, "VERSION") as t:
    __version__ = t.readline().strip()


__all__ = [
    "Capabilities",
    "Capability",
    "ChangeType",
    "register",
    "SmokestackCli",
    "Stack",
    "StackSet",
]
