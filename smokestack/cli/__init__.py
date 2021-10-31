from boto3.session import Session

from smokestack.abc.stack import StackABC
from smokestack.cli.arguments import make_operation_from_cli
from smokestack.config_manager import Configuration
from smokestack.exceptions import SmokestackError
from smokestack.models import OperationValues, PreviewOptions, Request


def invoke(request: Request) -> int:
    """Invokes `request` then returns the shell exit code."""

    Configuration.load(request.writer)

    op = make_operation_from_cli(request)

    if isinstance(op, int):
        return op

    stack = request.stacks[op.stack_key](session=Session(), writer=request.writer)

    operate(stack=stack, values=op.operation)

    return 0


class Operation:
    def __init__(self, values: OperationValues) -> None:
        self._values = values

    @property
    def deploy(self) -> bool:
        return self._values["deploy"]

    @property
    def preview(self) -> bool:
        return self._values["preview"]


def operate(stack: StackABC, values: OperationValues) -> None:
    op = Operation(values)
    with stack.create_change_set() as change:
        if op.preview:
            change.preview(PreviewOptions(empty_line_before_difference=True))
            if op.deploy:
                print()

        if op.deploy:
            change.execute()


def try_invoke(request: Request) -> int:
    try:
        return invoke(request)
    except SmokestackError as ex:
        request.writer.write(f"🔥 {str(ex)}\n")
        return 2


def invoke_then_exit(request: Request) -> None:
    """Invokes `request` then exits with the appropriate shell code."""

    exit(try_invoke(request))
