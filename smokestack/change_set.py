from time import time_ns
from typing import IO, Any, Optional

from ansiscape import green, heavy, yellow
from boto3.session import Session
from botocore.exceptions import WaiterError
from tabulate import tabulate

from smokestack.aws import endeavor
from smokestack.exceptions import ChangeSetCreationException
from smokestack.types import Capabilities, ChangeType


class ChangeSet:
    def __init__(
        self,
        capabilities: Capabilities,
        body: str,
        change_type: ChangeType,
        region: str,
        session: Session,
        stack_name: str,
        writer: IO[str],
    ) -> None:
        self.body = body
        self.capabilities = capabilities
        self.change_set_id: Optional[str] = None
        self.change_type = change_type
        self.client = session.client(
            "cloudformation",
            region_name=region,
        )  # pyright: reportUnknownMemberType=false
        self.has_changes: Optional[bool] = None
        self.executed = False
        self.region = region
        self.stack_name = stack_name
        self.writer = writer

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

        endeavor(self._try_execute, self._handle_execution_failure)
        endeavor(self._try_wait_for_execute)

    def _try_execute(self) -> None:
        if not self.change_set_id:
            raise Exception()

        self.writer.write("Executing change set...\n")
        self.client.execute_change_set(ChangeSetName=self.change_set_id)

    def _handle_execution_failure(self) -> None:
        response = self.client.describe_stack_events(StackName=self.stack_name)
        self.writer.write("\n\n" + str(response) + "\n\n")

    def _try_wait_for_execute(self) -> None:
        if not self.change_set_id:
            raise Exception()

        waiter = (
            self.client.get_waiter("stack_update_complete")
            if self.change_type == "UPDATE"
            else self.client.get_waiter("stack_create_complete")
        )

        waiter.wait(StackName=self.stack_name)
        self.executed = True

    def make_capabilities(self) -> None:
        pass

    def _try_create(self) -> None:

        self.writer.write(
            f"Creating change set for stack {yellow(self.stack_name)} in {yellow(self.region)}...\n"
        )

        try:
            response = self.client.create_change_set(
                StackName=self.stack_name,
                Capabilities=self.capabilities,
                ChangeSetName=f"t{time_ns()}",
                ChangeSetType=self.change_type,
                TemplateBody=self.body,
            )

        except self.client.exceptions.InsufficientCapabilitiesException as ex:
            error = ex.response.get("Error", {})
            raise ChangeSetCreationException(
                failure=error.get("Message", "insufficient capabilities"),
                stack_name=self.stack_name,
            )

        self.change_set_id = response["Id"]

    def _try_describe(self) -> None:
        if not self.change_set_id:
            raise Exception()

        response = self.client.describe_change_set(ChangeSetName=self.change_set_id)

        rows = [
            [
                heavy("Name").encoded,
                heavy("Type").encoded,
                heavy("Action").encoded,
                heavy("Replace?").encoded,
                heavy("Detail").encoded,
            ]
        ]

        for change in response["Changes"]:
            print(change)
            if resource_change := change.get("ResourceChange", None):
                print(resource_change)

                if resource_change["Action"] == "Add":
                    color = green
                else:
                    color = yellow

                rows.append(
                    [
                        color(resource_change["LogicalResourceId"]).encoded,
                        color(resource_change["ResourceType"]).encoded,
                        color(resource_change["Action"]).encoded,
                        color(resource_change.get("Replacement", "")).encoded,
                        color(
                            "\n".join(
                                [
                                    detail["Target"]["Name"]
                                    for detail in resource_change["Details"]
                                ]
                            )
                        ).encoded,
                    ]
                )
            else:
                print(f"⚠️ no resource change: {change}")

        t = tabulate(rows, headers="firstrow", tablefmt="plain")

        self.writer.write("\n" + t + "\n\n")

    def _try_delete(self) -> None:
        if not self.change_set_id:
            # The change set wasn't created, so there's nothing to delete:
            return

        if self.change_type == "CREATE":
            self.client.delete_stack(StackName=self.stack_name)
        else:
            self.client.delete_change_set(ChangeSetName=self.change_set_id)

    def _try_wait_for_creation(self) -> None:
        if not self.change_set_id:
            raise Exception()

        waiter = self.client.get_waiter("change_set_create_complete")

        try:
            waiter.wait(ChangeSetName=self.change_set_id)
            self.has_changes = True
        except WaiterError as ex:
            if ex.last_response:
                if reason := ex.last_response.get("StatusReason", None):
                    if "didn't contain changes" in str(reason):
                        self.has_changes = False
                        return
            raise

    def preview(self) -> None:
        if not self.has_changes:
            self.writer.write("There are no changes to apply.\n")
            return
        endeavor(self._try_describe)
