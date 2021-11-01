from sys import stdout
from typing import IO, Dict, Optional, Type

from smokestack.abc import StackABC
from smokestack.cli.arguments import make_operation_from_cli
from smokestack.config_manager import Configuration
from smokestack.exceptions import SmokestackError
from smokestack.models import Operation, PreviewOptions


class Session:
    def __init__(
        self,
        app_name: str,
        app_version: str,
        writer: Optional[IO[str]] = None,
    ) -> None:
        self.writer = writer or stdout
        Configuration.load()
        self._host = f"{app_name}/{app_version}"
        self._stacks: Dict[str, Type[StackABC]] = {}

    def _invoke(self) -> int:
        op = make_operation_from_cli(
            host=self._host,
            stack_keys=[k for k in self._stacks],
            writer=self.writer,
        )

        if isinstance(op, int):
            return op

        stack = self._stacks[op.stack_key](writer=self.writer)

        operation = Operation(op.operation)

        with stack.create_change_set() as change:
            if operation.preview:
                change.preview(PreviewOptions(empty_line_before_difference=True))
                if operation.deploy:
                    print()

            if operation.deploy:
                change.execute()

        return 0

    def invoke(self) -> int:
        try:
            return self._invoke()
        except SmokestackError as ex:
            self.writer.write(f"🔥 {str(ex)}\n")
            return 2

    def invoke_then_exit(self) -> None:
        """Invokes `request` then exits with the appropriate shell code."""

        exit(self.invoke())

    def register_stack(self, key: str, stack: Type[StackABC]) -> None:
        self._stacks.update({key: stack})
