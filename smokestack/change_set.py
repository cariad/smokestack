from time import time_ns
from typing import Any, Optional

from ansiscape import heavy
from botocore.exceptions import WaiterError
from stackdiff import StackDiff
from stackwhy import StackWhy

from smokestack.aws import endeavor
from smokestack.exceptions import (
    ChangeSetCreationError,
    ChangeSetExecutionError,
    SmokestackError,
)
from smokestack.types import ChangeSetArguments


class ChangeSet:
    """CloudFormation stack change set."""

    def __init__(self, args: ChangeSetArguments) -> None:
        self._args = args
        self._change_set_arn: Optional[str] = None
        self._executed = False
        self._has_changes: Optional[bool] = None
        self._has_rendered_no_changes = False
        self._stack_arn = args.stack if args.stack.startswith("arn:") else None
        self._stack_diff: Optional[StackDiff] = None

    def __enter__(self) -> "ChangeSet":
        endeavor(self._try_create)
        endeavor(self._try_wait_for_creation)
        return self

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        if not self._executed:
            endeavor(self._try_delete)

    def _handle_execution_failure(self) -> None:
        # Prefer the ARN if we have it:
        stack = self._stack_arn or self._args.stack
        sw = StackWhy(stack=stack, session=self._args.session)
        sw.render(self._args.out)
        raise ChangeSetExecutionError(stack_name=self._args.stack)

    def _try_create(self) -> None:
        client = self._args.session.client("cloudformation")

        try:
            response = client.create_change_set(
                StackName=self._args.stack,
                Capabilities=self._args.capabilities,
                ChangeSetName=f"t{time_ns()}",
                ChangeSetType=self._args.change_type,
                Parameters=self._args.parameters,
                TemplateBody=self._args.body,
            )

        except client.exceptions.InsufficientCapabilitiesException as ex:
            error = ex.response.get("Error", {})
            raise ChangeSetCreationError(
                failure=error.get("Message", "insufficient capabilities"),
                stack_name=self._args.stack,
            )

        except client.exceptions.ClientError as ex:
            raise ChangeSetCreationError(
                failure=str(ex),
                stack_name=self._args.stack,
            )

        self._change_set_arn = response["Id"]
        self._stack_arn = response["StackId"]

    def _try_delete(self) -> None:
        if self._change_set_arn is None:
            # The change set wasn't created, so there's nothing to delete:
            return

        client = self._args.session.client("cloudformation")

        if self._args.change_type == "CREATE":
            client.delete_stack(StackName=self._args.stack)
            return

        try:
            client.delete_change_set(ChangeSetName=self.change_set_arn)
        except client.exceptions.InvalidChangeSetStatusException:
            # We can't delete failed change sets, and that's okay.
            pass

    def _try_execute(self) -> None:
        # pyright: reportUnknownMemberType=false
        client = self._args.session.client("cloudformation")
        client.execute_change_set(ChangeSetName=self.change_set_arn)

    def _try_wait_for_creation(self) -> None:
        client = self._args.session.client("cloudformation")
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
        client = self._args.session.client("cloudformation")

        waiter = (
            client.get_waiter("stack_update_complete")
            if self._args.change_type == "UPDATE"
            else client.get_waiter("stack_create_complete")
        )

        waiter.wait(StackName=self._args.stack)
        self._args.out.write("\nExecuted successfully! 🎉\n")
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
        self._args.out.write("\nNo changes to apply.\n")
        self._has_rendered_no_changes = True

    def preview(self) -> None:
        if not self._has_changes:
            self.render_no_changes()
            return

        self._args.out.write("\n")
        self._args.out.write(f"{heavy('Template changes:').encoded} \n")
        self.visualizer.render_differences(self._args.out)
        self._args.out.write("\n")
        self.visualizer.render_changes(self._args.out)

    @property
    def visualizer(self) -> StackDiff:
        if not self._stack_diff:
            if self.change_set_arn is None:
                raise SmokestackError("Cannot visualise changes before creation")
            self._stack_diff = StackDiff(
                change=self.change_set_arn,
                stack=self._args.stack,
                session=self._args.session,
            )
        return self._stack_diff
