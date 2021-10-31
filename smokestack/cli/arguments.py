from argparse import ArgumentParser
from sys import argv
from typing import Union

from smokestack.config_manager import make_operation_from_config
from smokestack.models import Request, StackOperation
from smokestack.models.operation import OperationValues
from smokestack.version import get_version


def make_operation_from_cli(request: Request) -> Union[int, StackOperation]:
    parser = ArgumentParser(
        add_help=False,
        description="Deploys CloudFormation stacks, beautifully.",
    )

    parser.add_argument(
        "--ci",
        action="store_true",
        help='run configuration in "smokestack.yml"',
    )

    parser.add_argument(
        "--deploy",
        action="store_true",
        help='deploys the stack described by "--stack"',
    )

    parser.add_argument(
        "--help",
        action="store_true",
        help="prints help",
    )

    parser.add_argument(
        "--preview",
        action="store_true",
        help='previews the deployment of the stack described by "--stack"',
    )

    parser.add_argument(
        "--stack",
        choices=request.stacks.keys(),
        help="stack",
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="prints version",
    )

    args = argv if request.cli_args is None else request.cli_args
    parsed = parser.parse_args(args[1:])

    if parsed.help:
        request.writer.write(parser.format_help())
        return 0

    if parsed.version:
        host_version = f"{request.host.name}/{request.host.version}"
        request.writer.write(f"{host_version} smokestack/{get_version()}\n")
        return 0

    if not parsed.stack or parsed.stack not in request.stacks:
        keys = ",".join(request.stacks.keys())
        request.writer.write(f'🔥 "--stack {{{keys}}}" is required\n')
        return 1

    op = (
        make_operation_from_config(writer=request.writer)
        if parsed.ci
        else OperationValues(deploy=parsed.deploy, preview=parsed.preview)
    )

    return StackOperation(
        operation=op,
        stack_key=parsed.stack,
    )
