from smokestack.exceptions.smokestack import SmokestackError


class StackError(SmokestackError):
    def __init__(self, failure: str, operation: str, stack_name: str) -> None:
        super().__init__(f'Failed to {operation} stack "{stack_name}": {failure}')
