from typing import Dict, Type

from smokestack.stack_set import StackSet

_stack_sets: Dict[str, Type[StackSet]] = {}


def get_registered_stack_set(key: str) -> Type[StackSet]:
    return _stack_sets[key]


def register(key: str, stack_set: Type[StackSet]) -> None:
    """
    Registers a stack set to make it available via the command line.

    Arguments:
        key: Unique key to identify the stack set on the command line.

        stack_set: Stack set.
    """

    _stack_sets.update({key: stack_set})
