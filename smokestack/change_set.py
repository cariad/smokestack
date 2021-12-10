from io import StringIO
from logging import getLogger
from pathlib import Path
from time import time_ns
from typing import Any, Optional, Union

from ansiscape import heavy
from ansiscape.checks import should_emit_codes
from boto3.session import Session
from botocore.exceptions import WaiterError
from cfp.stack_parameters import StackParameters
from stackdiff import StackDiff
from stackwhy import StackWhy

from smokestack.aws import endeavor
from smokestack.exceptions import ChangeSetCreationError, ChangeSetExecutionError
from smokestack.stack import Stack
from smokestack.types import ChangeType


class ChangeSet:
    """
    A stack change set.

    Arguments:
        out: stdout proxy.
        stack: Stack to change.
    """

    def __init__(
        self,
        out: StringIO,
        stack: Stack,
        session: Optional[Session] = None,
    ) -> None:
        self._logger = getLogger("smokestack")
        self._session = session or Session(region_name=stack.region)

        self._cached_change_type: Optional[ChangeType] = None
        self._cached_stack_exists: Optional[bool] = None

        self._stack = stack
        self._change_set_arn: Optional[str] = None
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

    def __enter__(self) -> "ChangeSet":
        endeavor(self._try_create)
        endeavor(self._try_wait_for_create)
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

    def _render_no_changes(self) -> None:
        # Prevent an preview + execute run emitting "no changes" twice.
        if self._has_rendered_no_changes:
            return
        self._out.write("\nNo changes to apply.\n")
        self._has_rendered_no_changes = True

    def _try_create(self) -> None:
        stack_params = StackParameters()

        self._logger.debug("Populating parameters...")
        self._stack.parameters(stack_params)

        if stack_params.api_parameters:
            self._out.write("\n")
            stack_params.render(self._out)

        client = self._session.client("cloudformation")

        try:
            response = client.create_change_set(
                Capabilities=self._stack.capabilities,
                ChangeSetName=f"t{time_ns()}",
                ChangeSetType=self.change_type,
                Parameters=stack_params.api_parameters,
                StackName=self._stack.name,
                TemplateBody=self.get_body(self._stack.body),
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

        if self.change_type == "CREATE":
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

    def _try_wait_for_create(self) -> None:
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
            if self.change_type == "UPDATE"
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

    @property
    def change_type(self) -> ChangeType:
        """
        Describes whether this change will create or update the stack.
        """

        if self._cached_change_type is None:
            self._cached_change_type = "UPDATE" if self.stack_exists else "CREATE"

        return self._cached_change_type

    def execute(self) -> None:
        if not self._has_changes:
            self._render_no_changes()
            return

        endeavor(self._try_execute)
        endeavor(self._try_wait_for_execute, self._handle_execution_failure)

    @staticmethod
    def get_body(source: Union[Path, str]) -> str:
        if isinstance(source, str):
            return source

        with open(source, "r") as fp:
            return fp.read()

    def preview(self) -> None:
        if not self._has_changes:
            self._render_no_changes()
            return

        stack_diff = StackDiff(
            change=self.change_set_arn,
            session=self._session,
            stack=self._stack.name,
        )

        self._out.write("\n")

        line = "Template changes:"
        line = heavy(line).encoded if should_emit_codes() else line

        self._out.write(line)
        self._out.write("\n")
        stack_diff.render_differences(self._out)
        self._out.write("\n")
        stack_diff.render_changes(self._out)

    @property
    def stack_exists(self) -> bool:
        """
        Describes whether or not the stack already exists.
        """

        if self._cached_stack_exists is None:
            # pyright: reportUnknownMemberType=false
            client = self._session.client("cloudformation")

            try:
                client.describe_stacks(StackName=self._stack.name)
                self._cached_stack_exists = True
            except client.exceptions.ClientError:
                self._cached_stack_exists = False

        return self._cached_stack_exists
