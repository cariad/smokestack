from io import StringIO
from pathlib import Path
from typing import IO, Dict, Union

from botocore.exceptions import ClientError, WaiterError
from mock import ANY, Mock, patch
from pytest import fixture, mark, raises

from smokestack.change_set import ChangeSet
from smokestack.exceptions import ChangeSetCreationError, ChangeSetExecutionError
from smokestack.types.change_type import ChangeType
from tests.mocks import NoNeedsStack, WithNeedsStack

# pyright: reportPrivateUsage=false


@fixture
def change_set(out: StringIO, session: Mock) -> ChangeSet:
    return ChangeSet(out=out, session=session, stack=NoNeedsStack())


@fixture
def out() -> StringIO:
    return StringIO()


@fixture
def session() -> Mock:
    return Mock()


def test_change_set_arn__none(change_set: ChangeSet, out: StringIO) -> None:
    with raises(ValueError):
        change_set.change_set_arn
    assert out.getvalue() == ""


@mark.parametrize(
    "exists, expect",
    [
        (False, "CREATE"),
        (True, "UPDATE"),
    ],
)
def test_change_type(exists: bool, expect: ChangeType, change_set: ChangeSet) -> None:
    change_set._cached_stack_exists = exists
    assert change_set.change_type == expect


def test_execute(change_set: ChangeSet, out: StringIO) -> None:
    change_set._change_set_arn = "MyChangeSetArn"
    change_set._has_changes = True
    change_set.execute()
    assert change_set._executed
    assert out.getvalue() == "\nExecuted successfully! 🎉\n"


def test_execute__no_changes(change_set: ChangeSet, out: StringIO) -> None:
    change_set._has_changes = False
    change_set.execute()
    assert not change_set._executed
    assert out.getvalue() == "\nNo changes to apply.\n"


@mark.parametrize(
    "source, expect",
    [
        (Path("LICENSE"), "MIT License"),
        ("body", "body"),
    ],
)
def test_get_body(source: Union[Path, str], expect: str) -> None:
    assert ChangeSet.get_body(source).startswith(expect)


def test_handle_execution_failure(
    change_set: ChangeSet,
    out: StringIO,
    session: Mock,
) -> None:
    def mock_render(writer: StringIO) -> None:
        writer.write("Failure render goes here.\n")

    sw = Mock()
    sw.render = mock_render

    with patch("smokestack.change_set.StackWhy", return_value=sw) as sw_cls:
        with raises(ChangeSetExecutionError) as ex:
            change_set._handle_execution_failure()

    assert str(ex.value) == 'Failed to execute change set for stack "NoNeeds".'
    sw_cls.assert_called_once_with(stack="NoNeeds", session=session)
    assert out.getvalue() == "\n🔥 Execution failed:\n\nFailure render goes here.\n"


def test_preview(change_set: ChangeSet, session: Mock, out: StringIO) -> None:
    def mock_render_changes(writer: IO[str]) -> None:
        writer.write("Render changes here.\n")

    def mock_render_differences(writer: IO[str]) -> None:
        writer.write("Render differences here.\n")

    change_set._change_set_arn = "MyChangeSetArn"
    change_set._has_changes = True

    sd = Mock()
    sd.render_changes = mock_render_changes
    sd.render_differences = mock_render_differences

    with patch("smokestack.change_set.StackDiff", return_value=sd) as sd_cls:
        change_set.preview()

    sd_cls.assert_called_once_with(
        change="MyChangeSetArn",
        session=session,
        stack="NoNeeds",
    )

    assert (
        out.getvalue()
        == """
Template changes:
Render differences here.

Render changes here.
"""
    )


def test_preview__no_changes(change_set: ChangeSet, out: StringIO) -> None:
    change_set._has_changes = False

    with patch("smokestack.change_set.StackDiff") as sd_cls:
        change_set.preview()

    sd_cls.assert_not_called()
    assert out.getvalue() == "\nNo changes to apply.\n"


def test_render_no_changes(change_set: ChangeSet, out: StringIO) -> None:
    change_set._render_no_changes()
    assert out.getvalue() == "\nNo changes to apply.\n"


def test_render_no_changes_multiple(change_set: ChangeSet, out: StringIO) -> None:
    change_set._render_no_changes()
    change_set._render_no_changes()
    assert out.getvalue() == "\nNo changes to apply.\n"


def test_stack_exists__false(change_set: ChangeSet, session: Mock) -> None:
    describe_stacks = Mock(side_effect=Exception())

    exceptions = Mock()
    exceptions.ClientError = Exception

    cf = Mock()
    cf.exceptions = exceptions
    cf.describe_stacks = describe_stacks

    client = Mock(return_value=cf)
    session.client = client

    exists = change_set.stack_exists

    client.assert_called_once_with("cloudformation")
    describe_stacks.assert_called_once_with(StackName="NoNeeds")
    assert not exists


def test_stack_exists__true(change_set: ChangeSet, session: Mock) -> None:
    describe_stacks = Mock()

    cf = Mock()
    cf.describe_stacks = describe_stacks

    client = Mock(return_value=cf)
    session.client = client

    exists = change_set.stack_exists

    client.assert_called_once_with("cloudformation")
    describe_stacks.assert_called_once_with(StackName="NoNeeds")
    assert exists


def test_try_create() -> None:
    create_change_set = Mock(
        return_value={
            "Id": "response_id",
            "StackId": "response_stack_id",
        }
    )

    cf = Mock()
    cf.create_change_set = create_change_set

    client = Mock(return_value=cf)

    session = Mock()
    session.client = client

    out = StringIO()

    change_set = ChangeSet(out=out, session=session, stack=WithNeedsStack())
    change_set._cached_stack_exists = True
    change_set._try_create()

    client.assert_called_once_with("cloudformation")
    create_change_set.assert_called_once_with(
        Capabilities=[],
        ChangeSetName=ANY,
        ChangeSetType="UPDATE",
        Parameters=[],
        StackName="WithNeeds",
        TemplateBody=ANY,
    )

    assert change_set._change_set_arn == "response_id"
    assert change_set._stack_arn == "response_stack_id"
    assert out.getvalue() == ""


def test_try_create__client_error() -> None:
    exceptions = Mock()
    exceptions.InsufficientCapabilitiesException = ValueError
    exceptions.ClientError = ClientError

    create_change_set = Mock(
        side_effect=ClientError(
            {"Error": {"Message": "fire"}},
            "create_change_set",
        )
    )

    cf = Mock()
    cf.create_change_set = create_change_set
    cf.exceptions = exceptions

    client = Mock(return_value=cf)

    session = Mock()
    session.client = client

    out = StringIO()

    change_set = ChangeSet(out=out, session=session, stack=NoNeedsStack())
    change_set._cached_stack_exists = True

    with raises(ChangeSetCreationError) as ex:
        change_set._try_create()

    expect = 'Failed to create change set for stack "NoNeeds": An error occurred (Unknown) when calling the create_change_set operation: fire'

    assert str(ex.value) == expect
    assert out.getvalue() == "\nfoo = bar\n"

    assert change_set._change_set_arn is None
    assert change_set._stack_arn is None


def test_try_create__insufficient_capabilities() -> None:
    exceptions = Mock()
    exceptions.InsufficientCapabilitiesException = ClientError

    create_change_set = Mock(
        side_effect=ClientError(
            {"Error": {"Message": "fire"}},
            "create_change_set",
        )
    )

    cf = Mock()
    cf.create_change_set = create_change_set
    cf.exceptions = exceptions

    client = Mock(return_value=cf)

    session = Mock()
    session.client = client

    out = StringIO()

    change_set = ChangeSet(out=out, session=session, stack=NoNeedsStack())
    change_set._cached_stack_exists = True

    with raises(ChangeSetCreationError) as ex:
        change_set._try_create()

    assert str(ex.value) == 'Failed to create change set for stack "NoNeeds": fire'
    assert out.getvalue() == "\nfoo = bar\n"

    assert change_set._change_set_arn is None
    assert change_set._stack_arn is None


def test_try_create__with_parameters() -> None:
    create_change_set = Mock(
        return_value={
            "Id": "response_id",
            "StackId": "response_stack_id",
        }
    )

    cf = Mock()
    cf.create_change_set = create_change_set

    client = Mock(return_value=cf)

    session = Mock()
    session.client = client

    out = StringIO()

    change_set = ChangeSet(out=out, session=session, stack=NoNeedsStack())
    change_set._cached_stack_exists = True
    change_set._try_create()

    client.assert_called_once_with("cloudformation")
    create_change_set.assert_called_once_with(
        Capabilities=[],
        ChangeSetName=ANY,
        ChangeSetType="UPDATE",
        Parameters=[
            {
                "ParameterKey": "foo",
                "ParameterValue": "bar",
            }
        ],
        StackName="NoNeeds",
        TemplateBody=ANY,
    )

    assert change_set._change_set_arn == "response_id"
    assert change_set._stack_arn == "response_stack_id"
    assert out.getvalue() == "\nfoo = bar\n"


def test_try_delete__create(
    change_set: ChangeSet,
    out: StringIO,
    session: Mock,
) -> None:
    delete_stack = Mock()

    cf = Mock()
    cf.delete_stack = delete_stack

    client = Mock(return_value=cf)
    session.client = client

    change_set._cached_change_type = "CREATE"
    change_set._change_set_arn = "MyChangeSetArn"
    change_set._try_delete()

    client.assert_called_once_with("cloudformation")
    delete_stack.assert_called_once_with(StackName="NoNeeds")

    assert out.getvalue() == ""


def test_try_delete__none(
    change_set: ChangeSet,
    out: StringIO,
    session: Mock,
) -> None:
    client = Mock()
    session.client = client

    change_set._try_delete()

    client.assert_not_called()
    assert out.getvalue() == ""


def test_try_delete__update(
    change_set: ChangeSet,
    out: StringIO,
    session: Mock,
) -> None:
    delete_change_set = Mock()

    cf = Mock()
    cf.delete_change_set = delete_change_set

    client = Mock(return_value=cf)
    session.client = client

    change_set._cached_change_type = "UPDATE"
    change_set._change_set_arn = "MyChangeSetArn"
    change_set._try_delete()

    client.assert_called_once_with("cloudformation")
    delete_change_set.assert_called_once_with(ChangeSetName="MyChangeSetArn")

    assert out.getvalue() == ""


def test_try_delete__update__invalid_status(
    change_set: ChangeSet,
    out: StringIO,
    session: Mock,
) -> None:
    exceptions = Mock()
    exceptions.InvalidChangeSetStatusException = Exception

    delete_change_set = Mock(side_effect=Exception())

    cf = Mock()
    cf.delete_change_set = delete_change_set
    cf.exceptions = exceptions

    client = Mock(return_value=cf)
    session.client = client

    change_set._cached_change_type = "UPDATE"
    change_set._change_set_arn = "MyChangeSetArn"
    change_set._try_delete()

    client.assert_called_once_with("cloudformation")
    delete_change_set.assert_called_once_with(ChangeSetName="MyChangeSetArn")

    assert out.getvalue() == ""


def test_try_execute(
    change_set: ChangeSet,
    out: StringIO,
    session: Mock,
) -> None:
    execute_change_set = Mock()

    cf = Mock()
    cf.execute_change_set = execute_change_set

    client = Mock(return_value=cf)
    session.client = client

    change_set._change_set_arn = "MyChangeSetArn"
    change_set._try_execute()
    client.assert_called_once_with("cloudformation")
    execute_change_set.assert_called_once_with(ChangeSetName="MyChangeSetArn")
    assert out.getvalue() == ""


def test_try_wait_for_create(
    change_set: ChangeSet,
    out: StringIO,
    session: Mock,
) -> None:
    wait = Mock()

    waiter = Mock()
    waiter.wait = wait

    get_waiter = Mock(return_value=waiter)

    cf = Mock()
    cf.get_waiter = get_waiter

    client = Mock(return_value=cf)
    session.client = client

    change_set._change_set_arn = "MyChangeSetArn"
    change_set._try_wait_for_create()

    client.assert_called_once_with("cloudformation")
    get_waiter.assert_called_once_with("change_set_create_complete")
    wait.assert_called_once_with(ChangeSetName="MyChangeSetArn")
    assert change_set._has_changes
    assert out.getvalue() == ""


def test_try_wait_for_create__no_changes(
    change_set: ChangeSet,
    out: StringIO,
    session: Mock,
) -> None:
    last_response: Dict[str, str] = {"StatusReason": "didn't contain changes"}

    wait = Mock(
        side_effect=WaiterError(
            name="",
            reason="",
            # Boto3 types don't seem to match reality here:
            last_response=last_response,  # type: ignore
        )
    )

    waiter = Mock()
    waiter.wait = wait

    get_waiter = Mock(return_value=waiter)

    cf = Mock()
    cf.get_waiter = get_waiter

    client = Mock(return_value=cf)
    session.client = client

    change_set._change_set_arn = "MyChangeSetArn"
    change_set._try_wait_for_create()

    client.assert_called_once_with("cloudformation")
    get_waiter.assert_called_once_with("change_set_create_complete")
    wait.assert_called_once_with(ChangeSetName="MyChangeSetArn")
    assert not change_set._has_changes
    assert out.getvalue() == ""


def test_try_wait_for_create__waiter_error(
    change_set: ChangeSet,
    out: StringIO,
    session: Mock,
) -> None:
    wait = Mock(
        side_effect=WaiterError(
            name="",
            reason="fire",
            last_response={},
        )
    )

    waiter = Mock()
    waiter.wait = wait

    get_waiter = Mock(return_value=waiter)

    cf = Mock()
    cf.get_waiter = get_waiter

    client = Mock(return_value=cf)
    session.client = client

    change_set._change_set_arn = "MyChangeSetArn"

    with raises(WaiterError):
        change_set._try_wait_for_create()

    client.assert_called_once_with("cloudformation")
    get_waiter.assert_called_once_with("change_set_create_complete")
    wait.assert_called_once_with(ChangeSetName="MyChangeSetArn")
    assert not change_set._has_changes
    assert out.getvalue() == ""


def test_try_wait_for_create__waiter_error__unhandled_last_response(
    change_set: ChangeSet,
    out: StringIO,
    session: Mock,
) -> None:
    last_response: Dict[str, str] = {"foo": "fire"}

    wait = Mock(
        side_effect=WaiterError(
            name="",
            reason="",
            last_response=last_response,  # type: ignore
        )
    )

    waiter = Mock()
    waiter.wait = wait

    get_waiter = Mock(return_value=waiter)

    cf = Mock()
    cf.get_waiter = get_waiter

    client = Mock(return_value=cf)
    session.client = client

    change_set._change_set_arn = "MyChangeSetArn"

    with raises(WaiterError):
        change_set._try_wait_for_create()

    client.assert_called_once_with("cloudformation")
    get_waiter.assert_called_once_with("change_set_create_complete")
    wait.assert_called_once_with(ChangeSetName="MyChangeSetArn")
    assert not change_set._has_changes
    assert out.getvalue() == ""


def test_try_wait_for_create__waiter_error__unhandled_last_response_reason(
    change_set: ChangeSet,
    out: StringIO,
    session: Mock,
) -> None:
    last_response: Dict[str, str] = {"StatusReason": "fire"}

    wait = Mock(
        side_effect=WaiterError(
            name="",
            reason="",
            last_response=last_response,  # type: ignore
        )
    )

    waiter = Mock()
    waiter.wait = wait

    get_waiter = Mock(return_value=waiter)

    cf = Mock()
    cf.get_waiter = get_waiter

    client = Mock(return_value=cf)
    session.client = client

    change_set._change_set_arn = "MyChangeSetArn"

    with raises(WaiterError):
        change_set._try_wait_for_create()

    client.assert_called_once_with("cloudformation")
    get_waiter.assert_called_once_with("change_set_create_complete")
    wait.assert_called_once_with(ChangeSetName="MyChangeSetArn")
    assert not change_set._has_changes
    assert out.getvalue() == ""


@mark.parametrize(
    "change_type, expect_waiter",
    [
        ("CREATE", "stack_create_complete"),
        ("UPDATE", "stack_update_complete"),
    ],
)
def test_try_wait_for_execute(
    change_type: ChangeType,
    expect_waiter: str,
    change_set: ChangeSet,
    out: StringIO,
    session: Mock,
) -> None:
    wait = Mock()

    waiter = Mock()
    waiter.wait = wait

    get_waiter = Mock(return_value=waiter)

    cf = Mock()
    cf.get_waiter = get_waiter

    client = Mock(return_value=cf)
    session.client = client

    change_set._cached_change_type = change_type
    change_set._try_wait_for_execute()

    client.assert_called_once_with("cloudformation")
    get_waiter.assert_called_once_with(expect_waiter)
    wait.assert_called_once_with(StackName="NoNeeds")
    assert change_set._executed
    assert out.getvalue() == "\nExecuted successfully! 🎉\n"
