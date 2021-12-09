from pathlib import Path

from mock import Mock

from tests.mocks import NoNeedsStack, WithNeedsStack

# pyright: reportPrivateUsage=false


def test_change_set() -> None:

    describe_stacks = Mock()

    cf = Mock()
    cf.describe_stacks = describe_stacks

    client = Mock(return_value=cf)

    session = Mock()
    session.client = client

    stack = NoNeedsStack(session=session)

    change_set = stack.change_set()

    assert change_set._args.body == "NoNeeds template goes here."
    assert change_set._args.change_type == "UPDATE"


def test_exists__false() -> None:
    describe_stacks = Mock(side_effect=Exception())

    exceptions = Mock()
    exceptions.ClientError = Exception

    cf = Mock()
    cf.exceptions = exceptions
    cf.describe_stacks = describe_stacks

    client = Mock(return_value=cf)

    session = Mock()
    session.client = client

    stack = NoNeedsStack(session=session)

    exists = stack.exists

    client.assert_called_once_with("cloudformation")
    describe_stacks.assert_called_once_with(StackName="NoNeeds")
    assert not exists


def test_exists__true() -> None:
    describe_stacks = Mock()

    cf = Mock()
    cf.describe_stacks = describe_stacks

    client = Mock(return_value=cf)

    session = Mock()
    session.client = client

    stack = NoNeedsStack(session=session)

    exists = stack.exists

    client.assert_called_once_with("cloudformation")
    describe_stacks.assert_called_once_with(StackName="NoNeeds")
    assert exists


def test_resolved_body__path() -> None:
    stack = WithNeedsStack()
    assert isinstance(stack.body, Path)
    assert stack._resolved_body.startswith("MIT License")


def test_resolved_body__string() -> None:
    stack = NoNeedsStack()
    assert isinstance(stack.body, str)
    assert stack._resolved_body == "NoNeeds template goes here."
