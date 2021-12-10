from typing import Optional

from smokestack.exceptions.smokestack import SmokestackError


class StackError(SmokestackError):
    def __init__(
        self,
        operation: str,
        stack_name: str,
        failure: Optional[str] = None,
    ) -> None:
        fail_str = f": {failure}" if failure else "."
        super().__init__(f'Failed to {operation} stack "{stack_name}"{fail_str}')
