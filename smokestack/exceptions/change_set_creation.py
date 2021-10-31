from smokestack.exceptions.stack import StackError


class ChangeSetCreationError(StackError):
    def __init__(self, failure: str, stack_name: str) -> None:
        super().__init__(
            failure=failure,
            operation="create change set for",
            stack_name=stack_name,
        )
