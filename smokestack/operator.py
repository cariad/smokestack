from io import StringIO
from logging import getLogger
from multiprocessing import Process, Queue
from typing import Optional

from ansiscape import heavy, yellow
from ansiscape.checks import should_emit_codes

from smokestack.change_set import ChangeSet
from smokestack.protocols.stack_protocol import StackProtocol
from smokestack.types import Operation, OperationResult


class Operator(Process):
    def __init__(
        self,
        operation: Operation,
        queue: "Queue[OperationResult]",
        stack: StackProtocol,
    ) -> None:
        super().__init__()
        self._stack = stack
        self._queue = queue
        self._operation = operation

    def run(self) -> None:
        logger = getLogger("smokestack")

        logger.debug("Started operating on %s", self._stack.name)
        exception: Optional[Exception] = None

        out = StringIO()

        name = yellow(self._stack.name) if should_emit_codes else self._stack.name
        region = yellow(self._stack.region) if should_emit_codes else self._stack.region
        line = f"🌞 Stack {name} in {region}"
        line_fmt = heavy(line).encoded if should_emit_codes else line
        out.write(line_fmt)
        out.write("\n")

        try:
            with ChangeSet(stack=self._stack, out=out) as change:
                logger.debug("Created change set: %s", change)

                if self._operation.preview:
                    change.preview()

                if self._operation.execute:
                    change.execute()

        except Exception as ex:
            logger.exception("Change set operation failed.")
            exception = ex

        result = OperationResult(
            operation=self._operation,
            out=out,
            exception=str(exception) if exception else None,
            stack=type(self._stack),
        )

        self._queue.put(result)
