from dataclasses import dataclass

from smokestack.models.operation import OperationValues


@dataclass
class StackOperation:
    operation: OperationValues
    stack_key: str
