from typing import List, Type
from cline import CannotMakeArguments, CommandLineArguments
from mock import patch
from pytest import raises

from smokestack.tasks.operate import OperateTask, OperateTaskArguments
from smokestack.types import Operation
from smokestack.register import register
from smokestack import Stack, StackSet
from io import StringIO
from smokestack.exceptions import SmokestackError


class MockStackSet(StackSet):
    @property
    def stacks(self) -> List[Type[Stack]]:
        return []

execute_path = "tests.tasks.test_operate.MockStackSet.execute"


def test_invoke() -> None:
    register("mock", MockStackSet)

    operation=Operation(execute=False, preview=True)

    args = OperateTaskArguments(
        operation=operation,
        stack_set="mock",
    )

    out = StringIO()
    task = OperateTask(args, out)

    with patch(execute_path) as execute:
        exit_code = task.invoke()

    execute.assert_called_once_with(operation)
    assert exit_code == 0


def test_invoke__fail() -> None:
    register("mock", MockStackSet)

    operation=Operation(execute=False, preview=True)

    args = OperateTaskArguments(
        operation=operation,
        stack_set="mock",
    )

    out = StringIO()
    task = OperateTask(args, out)

    with patch(execute_path, side_effect=SmokestackError("fire")):
        exit_code = task.invoke()

    assert out.getvalue() == """
🔥 fire

"""
    assert exit_code == 1


def test_make_args__ci() -> None:
    args = CommandLineArguments(
        {
            "ci": True,
            "set": "foo",
        }
    )

    op = Operation(execute=True, preview=True)

    with patch("smokestack.tasks.operate.get_operation", return_value=op) as get_op:
        actual = OperateTask.make_args(args)

    get_op.assert_called_once()

    assert actual == OperateTaskArguments(
        log_level="WARNING",
        operation=op,
        stack_set="foo",
    )


def test_make_args__ci_and_execute() -> None:
    args = CommandLineArguments(
        {
            "ci": True,
            "execute": True,
            "set": "foo",
        }
    )

    with raises(CannotMakeArguments) as ex:
        OperateTask.make_args(args)

    assert str(ex.value) == "CI must be the only operation."


def test_make_args__execute_and_preview() -> None:
    args = CommandLineArguments(
        {
            "execute": True,
            "preview": True,
            "set": "foo",
        }
    )

    assert OperateTask.make_args(args) == OperateTaskArguments(
        log_level="WARNING",
        operation=Operation(execute=True, preview=True),
        stack_set="foo",
    )


def test_make_args__no_operation() -> None:
    args = CommandLineArguments(
        {
            "execute": False,
            "preview": False,
            "set": "foo",
        }
    )

    with raises(CannotMakeArguments) as ex:
        OperateTask.make_args(args)

    assert str(ex.value) == "Must execute and/or preview."
