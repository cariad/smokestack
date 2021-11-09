from typing import TypedDict


class StackParameter(TypedDict, total=False):
    ParameterKey: str
    ParameterValue: str
    UsePreviousValue: bool
    ResolvedValue: str
