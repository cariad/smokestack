from logging import getLogger

from mock import ANY, Mock
from mock.mock import patch

from smokestack.operator import Operator
from smokestack.types import Operation, OperationResult
from tests.mocks import NoNeedsStack

getLogger("smokestack").setLevel("DEBUG")


def test_run() -> None:
    operation = Operation(execute=True, preview=True)

    put = Mock()

    queue = Mock()
    queue.put = put

    execute = Mock()
    preview = Mock()

    cs = Mock()
    cs.__enter__ = Mock(return_value=cs)
    cs.__exit__ = Mock()
    cs.execute = execute
    cs.preview = preview

    cs_cls = Mock(return_value=cs)

    stack = NoNeedsStack()

    operator = Operator(
        operation=operation,
        queue=queue,
        stack=stack,
    )

    with patch("smokestack.operator.ChangeSet", return_value=cs) as cs_cls:
        operator.run()

    cs_cls.assert_called_once_with(stack=stack, out=ANY)

    preview.assert_called_once_with()
    execute.assert_called_once_with()

    expect = OperationResult(operation=operation, out=ANY, stack=type(stack))
    put.assert_called_once_with(expect)
