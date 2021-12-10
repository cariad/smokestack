from logging import getLogger

from mock import Mock
from mock.mock import ANY

from smokestack.operator import Operator
from smokestack.types import Operation, OperationResult

getLogger("smokestack").setLevel("DEBUG")


def test_run() -> None:
    operation = Operation(execute=True, preview=True)

    writer = Mock()

    put = Mock()

    queue = Mock()
    queue.put = put

    execute = Mock()
    preview = Mock()

    change_set = Mock()
    change_set.__enter__ = Mock(return_value=change_set)
    change_set.__exit__ = Mock()
    change_set.execute = execute
    change_set.preview = preview

    make_change_set = Mock(return_value=change_set)

    stack = Mock()
    stack.change_set = make_change_set
    stack.out = writer

    operator = Operator(
        operation=operation,
        queue=queue,
        stack=stack,
    )

    operator.run()

    make_change_set.assert_called_once_with(out=ANY)

    preview.assert_called_once_with()
    execute.assert_called_once_with()

    expect = OperationResult(operation=operation, out=ANY, stack=type(stack))
    put.assert_called_once_with(expect)
