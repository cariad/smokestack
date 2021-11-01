from smokestack.exceptions.stack import StackError


class ChangeSetExecutionError(StackError):
    def __init__(self, stack_name: str) -> None:
        super().__init__(
            failure="check log for details",
            operation="execute change set for",
            stack_name=stack_name,
        )
