class SmokestackException(Exception):
    pass


class StackException(SmokestackException):
    def __init__(self, failure: str, operation: str, stack_name: str) -> None:
        super().__init__(f'Failed to {operation} stack "{stack_name}": {failure}')


class ChangeSetCreationException(StackException):
    def __init__(self, failure: str, stack_name: str) -> None:
        super().__init__(
            failure=failure, operation="create change set for", stack_name=stack_name
        )
