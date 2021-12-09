from io import StringIO

from mock import Mock, patch
from mock.mock import ANY
from pytest import mark, raises

from smokestack.change_set import ChangeSet
from smokestack.exceptions import ChangeSetExecutionError
from smokestack.types import ChangeSetArguments, ChangeType

# pyright: reportPrivateUsage=false


def test_change_set_arn__none() -> None:
    args = ChangeSetArguments(
        body="",
        change_type="UPDATE",
        out=StringIO(),
        session=Mock(),
        stack="MyStack",
    )

    change_set = ChangeSet(args)

    with raises(ValueError):
        change_set.change_set_arn


def test_execute() -> None:
    out = StringIO()
    session = Mock()

    args = ChangeSetArguments(
        body="",
        change_type="UPDATE",
        out=out,
        session=session,
        stack="MyStack",
    )

    change_set = ChangeSet(args)
    change_set._change_set_arn = "MyChangeSetArn"
    change_set._has_changes = True
    change_set.execute()
    assert change_set._executed
    assert out.getvalue() == "\nExecuted successfully! 🎉\n"


def test_execute__no_changes() -> None:
    out = StringIO()
    session = Mock()

    args = ChangeSetArguments(
        body="",
        change_type="UPDATE",
        out=out,
        session=session,
        stack="MyStack",
    )

    change_set = ChangeSet(args)
    change_set._has_changes = False
    change_set.execute()
    assert not change_set._executed
    assert out.getvalue() == "\nNo changes to apply.\n"


def test_handle_execution_failure() -> None:
    out = StringIO()
    session = Mock()

    args = ChangeSetArguments(
        body="",
        change_type="UPDATE",
        out=out,
        session=session,
        stack="MyStack",
    )

    change_set = ChangeSet(args)

    render = Mock()

    sw = Mock()
    sw.render = render

    with patch("smokestack.change_set.StackWhy", return_value=sw) as sw_cls:
        with raises(ChangeSetExecutionError):
            change_set._handle_execution_failure()

    sw_cls.assert_called_once_with(stack="MyStack", session=session)
    assert out.getvalue() == ""


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

    args = ChangeSetArguments(
        body="template body",
        capabilities=["CAPABILITY_NAMED_IAM"],
        change_type="UPDATE",
        out=out,
        parameters=[
            {
                "ParameterKey": "foo",
                "ParameterValue": "bar",
            },
        ],
        session=session,
        stack="MyStack",
    )

    change_set = ChangeSet(args)
    change_set._try_create()
    client.assert_called_once_with("cloudformation")
    create_change_set.assert_called_once_with(
        StackName="MyStack",
        Capabilities=["CAPABILITY_NAMED_IAM"],
        ChangeSetName=ANY,
        ChangeSetType="UPDATE",
        Parameters=[
            {
                "ParameterKey": "foo",
                "ParameterValue": "bar",
            },
        ],
        TemplateBody="template body",
    )

    assert change_set._change_set_arn == "response_id"
    assert change_set._stack_arn == "response_stack_id"
    assert out.getvalue() == ""


def test_try_delete__create() -> None:
    delete_stack = Mock()

    cf = Mock()
    cf.delete_stack = delete_stack

    client = Mock(return_value=cf)

    session = Mock()
    session.client = client

    out = StringIO()

    args = ChangeSetArguments(
        body="",
        change_type="CREATE",
        out=out,
        session=session,
        stack="MyStack",
    )

    change_set = ChangeSet(args)
    change_set._change_set_arn = "MyChangeSetArn"
    change_set._try_delete()

    client.assert_called_once_with("cloudformation")
    delete_stack.assert_called_once_with(
        StackName="MyStack",
    )
    assert out.getvalue() == ""


def test_try_delete__update() -> None:
    delete_change_set = Mock()

    cf = Mock()
    cf.delete_change_set = delete_change_set

    client = Mock(return_value=cf)

    session = Mock()
    session.client = client

    out = StringIO()

    args = ChangeSetArguments(
        body="",
        change_type="UPDATE",
        out=out,
        session=session,
        stack="MyStack",
    )

    change_set = ChangeSet(args)
    change_set._change_set_arn = "MyChangeSetArn"
    change_set._try_delete()

    client.assert_called_once_with("cloudformation")
    delete_change_set.assert_called_once_with(
        ChangeSetName="MyChangeSetArn",
    )
    assert out.getvalue() == ""


def test_try_execute() -> None:
    execute_change_set = Mock()

    cf = Mock()
    cf.execute_change_set = execute_change_set

    client = Mock(return_value=cf)

    session = Mock()
    session.client = client

    out = StringIO()

    args = ChangeSetArguments(
        body="",
        change_type="UPDATE",
        out=out,
        session=session,
        stack="MyStack",
    )

    change_set = ChangeSet(args)
    change_set._change_set_arn = "MyChangeSetArn"
    change_set._try_execute()
    client.assert_called_once_with("cloudformation")
    execute_change_set.assert_called_once_with(ChangeSetName="MyChangeSetArn")
    assert out.getvalue() == ""


def test_try_wait_for_creation() -> None:
    wait = Mock()

    waiter = Mock()
    waiter.wait = wait

    get_waiter = Mock(return_value=waiter)

    cf = Mock()
    cf.get_waiter = get_waiter

    client = Mock(return_value=cf)

    session = Mock()
    session.client = client

    out = StringIO()

    args = ChangeSetArguments(
        body="",
        change_type="UPDATE",
        out=out,
        session=session,
        stack="MyStack",
    )

    change_set = ChangeSet(args)
    change_set._change_set_arn = "MyChangeSetArn"
    change_set._try_wait_for_creation()

    client.assert_called_once_with("cloudformation")
    get_waiter.assert_called_once_with("change_set_create_complete")
    wait.assert_called_once_with(ChangeSetName="MyChangeSetArn")
    assert change_set._has_changes
    assert out.getvalue() == ""


@mark.parametrize(
    "change_type, expect_waiter",
    [
        ("CREATE", "stack_create_complete"),
        ("UPDATE", "stack_update_complete"),
    ],
)
def test_try_wait_for_execute(change_type: ChangeType, expect_waiter: str) -> None:
    wait = Mock()

    waiter = Mock()
    waiter.wait = wait

    get_waiter = Mock(return_value=waiter)

    cf = Mock()
    cf.get_waiter = get_waiter

    client = Mock(return_value=cf)

    session = Mock()
    session.client = client

    out = StringIO()

    args = ChangeSetArguments(
        body="",
        change_type=change_type,
        out=out,
        session=session,
        stack="MyStack",
    )

    change_set = ChangeSet(args)
    change_set._try_wait_for_execute()

    client.assert_called_once_with("cloudformation")
    get_waiter.assert_called_once_with(expect_waiter)
    wait.assert_called_once_with(StackName="MyStack")
    assert change_set._executed
    assert out.getvalue() == "\nExecuted successfully! 🎉\n"
