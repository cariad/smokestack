from io import StringIO
from queue import Empty
from typing import Optional

from mock import ANY, Mock, patch
from pytest import fixture, raises

from smokestack import Stack, StackSet
from smokestack.enums import StackStatus
from smokestack.exceptions import SmokestackError
from smokestack.types import Operation, OperationResult
from tests.mocks import MockStackSet, NoNeedsStack, WithNeedsStack

# pyright: reportPrivateUsage=false


@fixture
def stack_set_out() -> StringIO:
    return StringIO()


@fixture
def stack_set(stack_set_out: StringIO) -> MockStackSet:
    return MockStackSet(stack_set_out)


def test_add_to_inbox__no_duplicates(stack_set: MockStackSet) -> None:
    stack_set._add_to_inbox(NoNeedsStack)
    stack_set._add_to_inbox(NoNeedsStack)
    assert len(stack_set._inbox) == 1


def test_add_to_inbox__no_needs(stack_set: MockStackSet) -> None:
    stack_set._add_to_inbox(NoNeedsStack)
    assert len(stack_set._inbox) == 1


def test_add_to_inbox__with_needs(stack_set: MockStackSet) -> None:
    stack_set._add_to_inbox(WithNeedsStack)
    assert len(stack_set._inbox) == 2


def test_execute(stack_set: MockStackSet, stack_set_out: StringIO) -> None:
    operation = Operation(execute=False, preview=True)

    def patched_start() -> None:
        stack_set._inbox = []

    operator = Mock()
    operator.start = patched_start

    stack: Optional[Stack] = None
    token: Optional[str] = None

    with patch("smokestack.stack_set.Operator", return_value=operator) as op_cls:
        stack_set.execute(operation)

        assert len(stack_set._wip) == 1

        for token in stack_set._wip:
            stack = stack_set._wip[token]

        assert token
        assert isinstance(stack, NoNeedsStack)

    op_cls.assert_called_once_with(
        operation=operation,
        queue=ANY,
        stack=stack,
        token=token,
    )

    assert (
        stack_set_out.getvalue()
        == """🌄 Starting NoNeeds in eu-west-1…
🥳 Done!
"""
    )


def test_get_needs_are_done__no_needs(stack_set: MockStackSet) -> None:
    stack_set._add_to_inbox(NoNeedsStack)
    stack = NoNeedsStack()
    assert stack_set._get_needs_are_done(stack)


def test_get_needs_are_done__with_needs(stack_set: MockStackSet) -> None:
    stack_set._add_to_inbox(WithNeedsStack)
    stack = WithNeedsStack()
    assert not stack_set._get_needs_are_done(stack)


def test_get_next_ready__no_needs(stack_set: MockStackSet) -> None:
    stack_set._add_to_inbox(NoNeedsStack)
    assert isinstance(stack_set._get_next_ready(), NoNeedsStack)


def test_get_next_ready__none(stack_set: MockStackSet) -> None:
    stack_set._add_to_inbox(WithNeedsStack)

    stack = stack_set._inbox[1]
    assert isinstance(stack, NoNeedsStack)
    stack_set._wip["000000"] = stack

    assert stack_set._get_next_ready() is None


def test_get_next_ready__with_needs(stack_set: MockStackSet) -> None:
    stack_set._add_to_inbox(WithNeedsStack)
    assert isinstance(stack_set._get_next_ready(), NoNeedsStack)


def test_get_status__done(stack_set: MockStackSet) -> None:
    assert stack_set._get_status(NoNeedsStack()) is StackStatus.DONE


def test_get_status__in_progress(stack_set: MockStackSet) -> None:
    stack_set._add_to_inbox(NoNeedsStack)
    stack = NoNeedsStack()
    stack_set._wip["000000"] = stack
    assert stack_set._get_status(stack) is StackStatus.IN_PROGRESS


def test_get_status__parent_with_need_in_progress(stack_set: MockStackSet) -> None:
    stack_set._add_to_inbox(WithNeedsStack)
    stack_set._wip["000000"] = NoNeedsStack()
    assert stack_set._get_status(WithNeedsStack()) is StackStatus.QUEUED


def test_get_status__need_in_progress(stack_set: MockStackSet) -> None:
    stack_set._add_to_inbox(WithNeedsStack)
    stack = stack_set._inbox[1]
    assert isinstance(stack, NoNeedsStack)
    stack_set._wip["000000"] = stack
    assert stack_set._get_status(stack) is StackStatus.IN_PROGRESS


def test_get_status__queued(stack_set: MockStackSet) -> None:
    stack_set._add_to_inbox(WithNeedsStack)
    stack = WithNeedsStack()
    assert stack_set._get_status(stack) is StackStatus.QUEUED


def test_get_status__ready(stack_set: MockStackSet) -> None:
    stack_set._add_to_inbox(NoNeedsStack)
    stack = NoNeedsStack()
    assert stack_set._get_status(stack) is StackStatus.READY


def test_handle_queued_done(stack_set: MockStackSet, stack_set_out: StringIO) -> None:
    stack = NoNeedsStack()

    stack_set._inbox = [stack]
    stack_set._wip["000000"] = stack

    out = StringIO()

    result = OperationResult(
        out=out,
        token="000000",
    )

    get = Mock(return_value=result)
    queue = Mock()
    queue.get = get

    out.write("Operation render goes here.\n")

    stack_set._handle_queued_done(queue)

    get.assert_called_once_with(block=True, timeout=1)

    assert not stack_set._inbox
    assert not stack_set._wip
    assert stack_set_out.getvalue() == "\nOperation render goes here.\n\n"


def test_handle_queued_done__no_result(stack_set: MockStackSet) -> None:
    stack_set._inbox = [NoNeedsStack()]
    stack_set._wip["000000"] = NoNeedsStack()

    get = Mock(side_effect=Empty())
    queue = Mock()
    queue.get = get

    stack_set._handle_queued_done(queue)

    get.assert_called_once_with(block=True, timeout=1)

    assert len(stack_set._inbox) == 1
    assert len(stack_set._wip) == 1


def test_handle_queued_done__raises(
    stack_set: MockStackSet,
    stack_set_out: StringIO,
) -> None:
    stack_set._inbox = [NoNeedsStack()]
    stack_set._wip["000000"] = NoNeedsStack()

    out = StringIO()

    result = OperationResult(
        exception="fire",
        out=out,
        token="000000",
    )

    get = Mock(return_value=result)
    queue = Mock()
    queue.get = get

    out.write("Operation render goes here.\n")

    with raises(SmokestackError) as ex:
        stack_set._handle_queued_done(queue)

    assert str(ex.value) == "fire"
    assert stack_set_out.getvalue() == "\nOperation render goes here.\n\n"


def test_inbox__empty_by_default(stack_set: MockStackSet) -> None:
    assert len(stack_set._inbox) == 0


def test_is_stack_type__false() -> None:
    StackSet._is_stack_type(NoNeedsStack(), WithNeedsStack)


def test_is_stack_type__true() -> None:
    StackSet._is_stack_type(NoNeedsStack(), NoNeedsStack)
