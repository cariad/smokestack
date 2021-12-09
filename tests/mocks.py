from pathlib import Path
from typing import List, Type

from cfp import StackParameters

from smokestack import Stack, StackSet


class NoNeedsStack(Stack):
    @property
    def body(self) -> str:
        return "NoNeeds template goes here."

    @property
    def name(self) -> str:
        return "NoNeeds"

    def parameters(self, params: StackParameters) -> None:
        params.add("foo", "bar")

    @property
    def region(self) -> str:
        return "eu-west-1"


class WithNeedsStack(Stack):
    @property
    def body(self) -> Path:
        return Path("LICENSE")

    @property
    def name(self) -> str:
        return "WithNeeds"

    @property
    def needs(self) -> List[Type[Stack]]:
        return [
            NoNeedsStack,
        ]

    @property
    def region(self) -> str:
        return "eu-west-2"


class MockStackSet(StackSet):
    @property
    def stacks(self) -> List[Type[Stack]]:
        return [
            WithNeedsStack,
        ]
