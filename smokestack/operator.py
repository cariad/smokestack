from io import StringIO
from logging import getLogger
from multiprocessing import Process, Queue
from typing import Optional

from smokestack.stack import Stack
from smokestack.types import Operation, OperationResult


class Operator(Process):
    def __init__(
        self,
        operation: Operation,
        queue: "Queue[OperationResult]",
        stack: Stack,
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

        try:
            with self._stack.change_set(out=out) as change:
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
