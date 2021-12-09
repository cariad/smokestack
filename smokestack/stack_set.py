from abc import ABC, abstractmethod
from logging import getLogger
from multiprocessing import Queue
from queue import Empty
from typing import IO, List, Optional, Type, cast

from ansiscape import heavy, yellow
from ansiscape.checks import should_emit_codes

from smokestack.enums import StackStatus
from smokestack.exceptions import SmokestackError
from smokestack.operator import Operator
from smokestack.protocols import StackProtocol
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
        self._wip: List[Stack] = []

    def _add_to_inbox(self, stack_type: Type[Stack]) -> None:
        """Adds a stack type and all of its needs to the inbox."""

        if self._get_listed(stack_type, self._inbox):
            # If this has been added already then assume its needs have too.
            return

        stack = stack_type()
        self._inbox.append(stack)

        for need in stack.needs:
            self._add_to_inbox(need)

    def _get_listed(
        self,
        stack_type: Type[StackProtocol],
        src: List[Stack],
    ) -> Optional[Stack]:
        """Gets the stack instance of the given type."""

        for stack in src:
            # A bit cheeky, but let's assume nothing else inherits from StackProtocol.
            concrete_type = cast(Type[Stack], stack_type)
            if self._is_stack_type(stack, concrete_type):
                return stack

        return None

    def _get_needs_are_done(self, stack: Stack) -> bool:
        for needs_type in stack.needs:
            if need := self._get_listed(needs_type, self._inbox):
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
        if not self._get_listed(type(stack), self._inbox):
            return StackStatus.DONE
        if self._get_listed(type(stack), self._wip):
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

        stack = self._get_listed(result.stack, self._inbox)

        if not stack:
            raise SmokestackError(f"{result.stack} not in inbox.")

        name = yellow(stack.name) if should_emit_codes else stack.name
        region = yellow(stack.region) if should_emit_codes else stack.region
        line = f"🌞 Stack {name} in {region}"
        line_fmt = heavy(line).encoded if should_emit_codes else line
        self._out.write(line_fmt)
        self._out.write("\n")

        # pyright: reportPrivateUsage=false
        if stack._stack_parameters:
            heading = "Parameters:"
            heading_fmt = heavy(heading) if should_emit_codes else heading
            self._out.write(f"\n{heading_fmt}\n")
            stack._stack_parameters.render(self._out)

        if result.exception:
            raise SmokestackError(result.exception)

        self._last_write_was_result = True

        self._remove_listed(result.stack, self._inbox)
        self._remove_listed(result.stack, self._wip)

    @staticmethod
    def _is_stack_type(stack: Stack, stack_type: Type[Stack]) -> bool:
        return isinstance(
            stack,
            stack_type,
        )  # pyright: reportUnnecessaryIsInstance=false

    def execute(self, op: Operation) -> None:
        """
        Executes an operation on the stack set.

        Arguments:
            op: Operation.
        """

        self._logger.debug("Started executing: %s", self.__class__.__name__)

        for stack in self.stacks:
            self._add_to_inbox(stack)

        queue: "Queue[OperationResult]" = Queue(3)

        while self._inbox:

            if self._wip:
                self._handle_queued_done(queue)

            if queue.full():
                continue

            if ready := self._get_next_ready():
                self._out.write(f"🌄 Starting {yellow(ready.name)}…\n")
                self._last_write_was_result = False
                self._wip.append(ready)
                Operator(operation=op, queue=queue, stack=ready).start()

        self._out.write("🥳 Done!\n")

    def _remove_listed(self, stack_type: Type[StackProtocol], src: List[Stack]) -> None:
        if stack := self._get_listed(stack_type, src):
            src.remove(stack)
        else:
            self._logger.warning("%s complete but not in %s.", stack_type, src)

    @property
    @abstractmethod
    def stacks(self) -> List[Type[Stack]]:
        """
        Gets the stacks in this set.

        In this example, the "Application" set includes an application, database
        and logging stack:

        .. code-block:: python

            from smokestack import StackSet

            import myproject.stacks


            class ApplicationStackSet(StackSet):

                # ...

                @property
                def stacks(self) -> List[Type[Stack]]:
                    return [
                        myproject.stacks.ApplicationStack,
                        myproject.stacks.DatabaseStack,
                        myproject.stacks.LoggingStack,
                    ]

        Note that the deployment order is prescribed by each stack's
        :py:attr:`smokestack.Stack.needs` property.
        """
