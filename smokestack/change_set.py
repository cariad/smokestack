from time import time_ns
from typing import IO, Any, Literal, Optional, TypedDict, Union

from ansiscape import heavy
from boto3.session import Session
from botocore.exceptions import WaiterError
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


class ChangeSetArgs(TypedDict):
    capabilities: Capabilities
    body: str
    change_type: ChangeType
    session: Session
    stack_name: str
    writer: IO[str]


class ChangeSet(ChangeSetABC):
    """
    Arguments:
        stack: Stack ARN, ID or name
    """

    def __init__(self, args: ChangeSetArgs) -> None:
        self.body = args["body"]
        self.capabilities = args["capabilities"]
        self.change_set_id: Optional[str] = None
        self.change_type = args["change_type"]
        self.has_changes: Optional[bool] = None
        self.executed = False
        self.session = args["session"]
        self.stack = args["stack_name"]
        self.writer = args["writer"]

        self.client = self.session.client(
            "cloudformation",
        )  # pyright: reportUnknownMemberType=false

        self._stack_arn = self.stack if self.is_arn(self.stack) else None
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

        self.writer.write("Executing change set...\n")
        self.client.execute_change_set(ChangeSetName=self.change_set_arn)

    @property
    def stack_arn(self) -> Optional[str]:
        return self._stack_arn

    def _handle_execution_failure(self) -> None:
        # Prefer the ARN if we have it:
        stack = self.stack_arn or self.stack
        self.writer.write("\n")
        sw = StackWhy(stack=stack, session=self.session)
        sw.render(self.writer)
        raise ChangeSetExecutionError(stack_name=self.stack)

    def _try_wait_for_execute(self) -> None:
        waiter = self.client.get_waiter(self.stack_waiter_type)

        waiter.wait(StackName=self.stack)
        self.executed = True
        self.writer.write("Executed successfully! 🎉\n")

    def make_capabilities(self) -> None:
        pass

    def _try_create(self) -> None:
        self.writer.write("Creating change set...\n")

        try:
            response = self.client.create_change_set(
                StackName=self.stack,
                Capabilities=self.capabilities,
                ChangeSetName=f"t{time_ns()}",
                ChangeSetType=self.change_type,
                TemplateBody=self.body,
            )

        except self.client.exceptions.InsufficientCapabilitiesException as ex:
            error = ex.response.get("Error", {})
            raise ChangeSetCreationError(
                failure=error.get("Message", "insufficient capabilities"),
                stack_name=self.stack,
            )

        except self.client.exceptions.ClientError as ex:
            raise ChangeSetCreationError(
                failure=str(ex),
                stack_name=self.stack,
            )

        self.change_set_arn = response["Id"]
        self._stack_arn = response["StackId"]

    def _try_delete(self) -> None:
        if not self.change_set_arn:
            # The change set wasn't created, so there's nothing to delete:
            return

        if self.change_type == "CREATE":
            self.client.delete_stack(StackName=self.stack)
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
            self.writer.write("There are no changes to apply.\n")
            return

        options = options or PreviewOptions()

        if options.empty_line_before_difference:
            self.writer.write("\n")

        self.writer.write(f"{heavy('Stack changes:').encoded} \n")
        self.visualizer.render_differences(self.writer)
        self.writer.write("\n")
        self.visualizer.render_changes(self.writer)

    @property
    def visualizer(self) -> StackDiff:
        if not self._stack_diff:
            if self.change_set_arn is None:
                raise SmokestackError("Cannot visualise changes before creation")
            self._stack_diff = StackDiff(
                change=self.change_set_arn,
                stack=self.stack,
                session=self.session,
            )
        return self._stack_diff

    @property
    def stack_waiter_type(
        self,
    ) -> Union[Literal["stack_update_complete"], Literal["stack_create_complete"]]:
        return (
            "stack_update_complete"
            if self.change_type == "UPDATE"
            else "stack_create_complete"
        )
