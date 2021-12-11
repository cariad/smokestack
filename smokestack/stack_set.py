from abc import ABC, abstractmethod
from logging import getLogger
from multiprocessing import Queue
from queue import Empty
from typing import IO, Dict, List, Optional, Type
from uuid import uuid4

from ansiscape import yellow
from ansiscape.checks import should_emit_codes

from smokestack.enums import StackStatus
from smokestack.exceptions import SmokestackError
from smokestack.operator import Operator
from smokestack.stack import Stack
from smokestack.types import Operation, OperationResult


class StackSet(ABC):
    """
    A set of stacks.
    """

    def __init__(self, out: IO[str]) -> None:
        self._inbox: List[Stack] = []
        """
        Flat list of stacks waiting to be executed.
        """

        self._last_write_was_result = False
        self._logger = getLogger("smokestack")
        self._out = out
        self._wip: Dict[str, Stack] = {}

    def _add_to_inbox(self, stack_type: Type[Stack]) -> None:
        """Adds a stack type and all of its needs to the inbox."""

        if self._is_in_inbox(stack_type):
            # If this has been added already then assume its needs have too.
            return

        stack = stack_type()
        self._inbox.append(stack)

        for need in stack.needs:
            self._add_to_inbox(need)

    def _is_in_inbox(
        self,
        stack_type: Type[Stack],
    ) -> Optional[Stack]:
        """Gets the stack instance of the given type."""

        for stack in self._inbox:
            if self._is_stack_type(stack, stack_type):
                return stack

        return None

    def _get_needs_are_done(self, stack: Stack) -> bool:
        for needs_type in stack.needs:
            if need := self._is_in_inbox(needs_type):
                self._logger.debug(
                    "%s not ready: need %s is not done.",
                    stack.name,
                    need.name,
                )
                return False

        return True

    def _get_next_ready(self) -> Optional[Stack]:
        for stack in self._inbox:
            if self._get_status(stack) == StackStatus.READY:
                return stack
        return None

    def _get_status(self, stack: Stack) -> StackStatus:
        if not self._is_in_inbox(type(stack)):
            return StackStatus.DONE
        if stack in self._wip.values():
            return StackStatus.IN_PROGRESS
        if self._get_needs_are_done(stack):
            return StackStatus.READY
        return StackStatus.QUEUED

    def _handle_queued_done(self, queue: "Queue[OperationResult]") -> None:
        try:
            # Don't wait too long: there might be queued stacks ready to start.
            result = queue.get(block=True, timeout=1)
        except Empty:
            return

        if not self._last_write_was_result:
            self._out.write("\n")

        self._out.write(result.out.getvalue())
        self._out.write("\n")
        self._last_write_was_result = True

        if result.exception:
            self._logger.warning("Background job raised: %s", result.exception)
            raise SmokestackError(result.exception)

        stack = self._wip[result.token]

        del self._wip[result.token]

        try:
            self._inbox.remove(stack)
        except ValueError:
            raise SmokestackError(
                f"{stack.name} was operated on, but not found in the work queue."
            )

    @staticmethod
    def _is_stack_type(stack: Stack, stack_type: Type[Stack]) -> bool:
        return isinstance(
            stack,
            stack_type,
        )  # pyright: reportUnnecessaryIsInstance=false

    def execute(self, operation: Operation) -> None:
        """
        Executes an operation on the stack set.

        Arguments:
            operation: Operation.
        """

        self._logger.debug("Started executing: %s", self.__class__.__name__)

        for stack in self.stacks:
            self._add_to_inbox(stack)

        color = should_emit_codes()
        queue: "Queue[OperationResult]" = Queue(3)

        while self._inbox:

            if self._wip:
                self._handle_queued_done(queue)

            if queue.full():
                continue

            if ready := self._get_next_ready():
                name = yellow(ready.name) if color else ready.name
                region = yellow(ready.region) if color else ready.region

                self._out.write(f"🌄 Starting {name} in {region}…\n")
                self._last_write_was_result = False

                token = str(uuid4())
                self._wip[token] = ready

                operator = Operator(
                    operation=operation,
                    queue=queue,
                    stack=ready,
                    token=token,
                )

                operator.start()

        self._out.write("🥳 Done!\n")

    @property
    @abstractmethod
    def stacks(self) -> List[Type[Stack]]:
        """
        Gets the stacks in this set.
        """
