from io import StringIO
from logging import getLogger
from time import time_ns
from typing import Any, Optional

from ansiscape import heavy
from boto3.session import Session
from botocore.exceptions import WaiterError
from cfp.stack_parameters import StackParameters
from stackdiff import StackDiff
from stackwhy import StackWhy

from smokestack.aws import endeavor
from smokestack.exceptions import (
    ChangeSetCreationError,
    ChangeSetExecutionError,
    SmokestackError,
)
from smokestack.protocols import StackProtocol
from smokestack.types import ChangeType


class ChangeSet:
    """
    A stack change set.
    """

    def __init__(self, stack: StackProtocol, out: StringIO) -> None:
        self._logger = getLogger("smokestack")
        self._session = Session(region_name=stack.region)

        exists = self.stack_exists(name=stack.name, session=self._session)

        self._stack = stack
        self._change_set_arn: Optional[str] = None
        self._change_type: ChangeType = "UPDATE" if exists else "CREATE"
        self._executed = False
        self._has_changes: Optional[bool] = None
        self._has_rendered_no_changes = False
        self._out = out

        # We only need the stack's ARN when we're handling an execution failure.
        # We'll gather the ARN when we create the change set then pass it to
        # StackWhy if we need to render a boner.
        self._stack_arn: Optional[str] = None
        """
        The stack's ARN (if it's known).
        """

        self._stack_diff: Optional[StackDiff] = None

    @staticmethod
    def stack_exists(name: str, session: Session) -> bool:
        """
        Returns `True` if the stack exists, otherwise `False`.
        """

        # pyright: reportUnknownMemberType=false
        client = session.client("cloudformation")

        try:
            client.describe_stacks(StackName=name)
            return True
        except client.exceptions.ClientError:
            return False

    def __enter__(self) -> "ChangeSet":
        endeavor(self._try_create)
        endeavor(self._try_wait_for_creation)
        return self

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        if not self._executed:
            endeavor(self._try_delete)

    def _handle_execution_failure(self) -> None:
        # Prefer the ARN if we have it:
        stack_id = self._stack_arn or self._stack.name
        self._logger.warning("Handling an execution failure on: %s", stack_id)
        self._out.write("\n🔥 Execution failed:\n\n")
        StackWhy(stack=stack_id, session=self._session).render(self._out)
        raise ChangeSetExecutionError(stack_name=self._stack.name)

    def _try_create(self) -> None:

        body = self._stack.body
        resolved_body = body if isinstance(body, str) else open(body, "r").read()

        client = self._session.client("cloudformation")

        self._logger.debug("Populating parameters...")

        stack_params = StackParameters()
        self._stack.parameters(stack_params)

        if stack_params.api_parameters:
            self._out.write("\n")
            stack_params.render(self._out)

        try:
            response = client.create_change_set(
                StackName=self._stack.name,
                Capabilities=self._stack.capabilities,
                ChangeSetName=f"t{time_ns()}",
                ChangeSetType=self._change_type,
                Parameters=stack_params.api_parameters,
                TemplateBody=resolved_body,
            )

        except client.exceptions.InsufficientCapabilitiesException as ex:
            error = ex.response.get("Error", {})
            raise ChangeSetCreationError(
                failure=error.get("Message", "insufficient capabilities"),
                stack_name=self._stack.name,
            )

        except client.exceptions.ClientError as ex:
            raise ChangeSetCreationError(
                failure=str(ex),
                stack_name=self._stack.name,
            )

        self._change_set_arn = response["Id"]
        self._stack_arn = response["StackId"]

    def _try_delete(self) -> None:
        if self._change_set_arn is None:
            # The change set wasn't created, so there's nothing to delete:
            return

        client = self._session.client("cloudformation")

        if self._change_type == "CREATE":
            client.delete_stack(StackName=self._stack.name)
            return

        try:
            client.delete_change_set(ChangeSetName=self.change_set_arn)
        except client.exceptions.InvalidChangeSetStatusException:
            # We can't delete failed change sets, and that's okay.
            pass

    def _try_execute(self) -> None:
        # pyright: reportUnknownMemberType=false
        client = self._session.client("cloudformation")
        client.execute_change_set(ChangeSetName=self.change_set_arn)

    def _try_wait_for_creation(self) -> None:
        client = self._session.client("cloudformation")
        waiter = client.get_waiter("change_set_create_complete")

        try:
            waiter.wait(ChangeSetName=self.change_set_arn)
            self._has_changes = True
        except WaiterError as ex:
            if ex.last_response:
                if reason := ex.last_response.get("StatusReason", None):
                    if "didn't contain changes" in str(reason):
                        self._has_changes = False
                        return
            raise

    def _try_wait_for_execute(self) -> None:
        client = self._session.client("cloudformation")

        waiter = (
            client.get_waiter("stack_update_complete")
            if self._change_type == "UPDATE"
            else client.get_waiter("stack_create_complete")
        )

        waiter.wait(StackName=self._stack.name)
        self._out.write("\nExecuted successfully! 🎉\n")
        self._executed = True

    @property
    def change_set_arn(self) -> str:
        """Gets this change set's ARN."""

        if self._change_set_arn is None:
            raise ValueError("No change set ARN")
        return self._change_set_arn

    def execute(self) -> None:
        if not self._has_changes:
            self.render_no_changes()
            return

        endeavor(self._try_execute)
        endeavor(self._try_wait_for_execute, self._handle_execution_failure)

    def render_no_changes(self) -> None:
        # Prevent an preview + execute run emitting "no changes" twice.
        if self._has_rendered_no_changes:
            return
        self._out.write("\nNo changes to apply.\n")
        self._has_rendered_no_changes = True

    def preview(self) -> None:
        if not self._has_changes:
            self.render_no_changes()
            return

        self._out.write("\n")
        self._out.write(f"{heavy('Template changes:').encoded} \n")
        self.visualizer.render_differences(self._out)
        self._out.write("\n")
        self.visualizer.render_changes(self._out)

    @property
    def visualizer(self) -> StackDiff:
        if not self._stack_diff:
            if self.change_set_arn is None:
                raise SmokestackError("Cannot visualise changes before creation")
            self._stack_diff = StackDiff(
                change=self.change_set_arn,
                stack=self._stack.name,
                session=self._session,
            )
        return self._stack_diff
