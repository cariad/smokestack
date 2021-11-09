from dataclasses import dataclass
from time import time_ns
from typing import IO, Any, List, Literal, Optional, Union

from ansiscape import heavy
from boto3.session import Session
from botocore.exceptions import WaiterError
from cfp import ApiParameter
from stackdiff import StackDiff
from stackwhy import StackWhy

from smokestack.abc import ChangeSetABC
from smokestack.aws import endeavor
from smokestack.exceptions import (
    ChangeSetCreationError,
    ChangeSetExecutionError,
    SmokestackError,
)
from smokestack.models import PreviewOptions
from smokestack.types import Capabilities, ChangeType


@dataclass
class ChangeSetArgs:
    capabilities: Capabilities
    body: str
    change_type: ChangeType
    parameters: List[ApiParameter]
    session: Session
    stack: str
    writer: IO[str]


class ChangeSet(ChangeSetABC):
    """
    Arguments:
        stack: Stack ARN, ID or name
    """

    def __init__(self, args: ChangeSetArgs) -> None:
        self.args = args
        # self.capabilities = args["capabilities"]
        self.change_set_id: Optional[str] = None
        # self.change_type = args["change_type"]
        self.has_changes: Optional[bool] = None
        self.executed = False
        # self.parameters = args["parameters"]
        # self.session = args["session"]
        # self.stack = args["stack_name"]
        # self.writer = args["writer"]

        self.client = self.args.session.client(
            "cloudformation",
        )  # pyright: reportUnknownMemberType=false

        self._stack_arn = self.args.stack if self.is_arn(self.args.stack) else None
        self._stack_diff: Optional[StackDiff] = None

    @staticmethod
    def is_arn(value: str) -> bool:
        return value.startswith("arn:")

    def __enter__(self) -> "ChangeSet":
        endeavor(self._try_create)
        endeavor(self._try_wait_for_creation)
        return self

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        if not self.executed:
            endeavor(self._try_delete)

    def execute(self) -> None:
        if not self.has_changes:
            return

        endeavor(self._try_execute)
        endeavor(self._try_wait_for_execute, self._handle_execution_failure)

    def _try_execute(self) -> None:
        if not self.change_set_arn:
            raise Exception()

        self.args.writer.write("Executing change set...\n")
        self.client.execute_change_set(ChangeSetName=self.change_set_arn)

    @property
    def stack_arn(self) -> Optional[str]:
        return self._stack_arn

    def _handle_execution_failure(self) -> None:
        # Prefer the ARN if we have it:
        stack = self.stack_arn or self.args.stack
        self.args.writer.write("\n")
        sw = StackWhy(stack=stack, session=self.args.session)
        sw.render(self.args.writer)
        raise ChangeSetExecutionError(stack_name=self.args.stack)

    def _try_wait_for_execute(self) -> None:
        waiter = self.client.get_waiter(self.stack_waiter_type)

        waiter.wait(StackName=self.args.stack)
        self.executed = True
        self.args.writer.write("Executed successfully! 🎉\n")

    def make_capabilities(self) -> None:
        pass

    def _try_create(self) -> None:
        self.args.writer.write("Creating change set...\n")

        try:
            response = self.client.create_change_set(
                StackName=self.args.stack,
                Capabilities=self.args.capabilities,
                ChangeSetName=f"t{time_ns()}",
                ChangeSetType=self.args.change_type,
                Parameters=self.args.parameters,
                TemplateBody=self.args.body,
            )

        except self.client.exceptions.InsufficientCapabilitiesException as ex:
            error = ex.response.get("Error", {})
            raise ChangeSetCreationError(
                failure=error.get("Message", "insufficient capabilities"),
                stack_name=self.args.stack,
            )

        except self.client.exceptions.ClientError as ex:
            raise ChangeSetCreationError(
                failure=str(ex),
                stack_name=self.args.stack,
            )

        self.change_set_arn = response["Id"]
        self._stack_arn = response["StackId"]

    def _try_delete(self) -> None:
        if not self.change_set_arn:
            # The change set wasn't created, so there's nothing to delete:
            return

        if self.args.change_type == "CREATE":
            self.client.delete_stack(StackName=self.args.stack)
            return

        try:
            self.client.delete_change_set(ChangeSetName=self.change_set_arn)
        except self.client.exceptions.InvalidChangeSetStatusException:
            # We can't delete failed change sets, and that's okay.
            pass

    def _try_wait_for_creation(self) -> None:
        if not self.change_set_arn:
            raise Exception()

        waiter = self.client.get_waiter("change_set_create_complete")

        try:
            waiter.wait(ChangeSetName=self.change_set_arn)
            self.has_changes = True
        except WaiterError as ex:
            if ex.last_response:
                if reason := ex.last_response.get("StatusReason", None):
                    if "didn't contain changes" in str(reason):
                        self.has_changes = False
                        return
            raise

    def preview(self, options: Optional[PreviewOptions] = None) -> None:
        if not self.has_changes:
            self.args.writer.write("There are no changes to apply.\n")
            return

        options = options or PreviewOptions()

        if options.empty_line_before_difference:
            self.args.writer.write("\n")

        self.args.writer.write(f"{heavy('Stack changes:').encoded} \n")
        self.visualizer.render_differences(self.args.writer)
        self.args.writer.write("\n")
        self.visualizer.render_changes(self.args.writer)

    @property
    def visualizer(self) -> StackDiff:
        if not self._stack_diff:
            if self.change_set_arn is None:
                raise SmokestackError("Cannot visualise changes before creation")
            self._stack_diff = StackDiff(
                change=self.change_set_arn,
                stack=self.args.stack,
                session=self.args.session,
            )
        return self._stack_diff

    @property
    def stack_waiter_type(
        self,
    ) -> Union[Literal["stack_update_complete"], Literal["stack_create_complete"]]:
        return (
            "stack_update_complete"
            if self.args.change_type == "UPDATE"
            else "stack_create_complete"
        )
