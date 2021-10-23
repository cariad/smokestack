from argparse import ArgumentParser
from dataclasses import dataclass
from sys import argv, stdout
from typing import IO, Dict, List, Optional, Type

from boto3.session import Session

from smokestack.exceptions import SmokestackException
from smokestack.stack import Stack
from smokestack.version import get_version


@dataclass
class Host:
    """Information about the host application."""

    name: str
    """Host application name."""

    version: str
    """Host application version."""


@dataclass
class Request:
    host: Host
    """Host application."""

    stacks: Dict[str, Type[Stack]]
    """Deployable stacks."""

    cli_args: Optional[List[str]] = None
    """CLI arguments. Will determinate automatically by default."""

    writer: IO[str] = stdout
    """Output writer. Will use `stdout` by default."""


def invoke(request: Request) -> int:
    """Invokes `request` then returns the shell exit code."""

    parser = ArgumentParser(
        add_help=False,
        description="Deploys CloudFormation stacks, beautifully.",
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

    cli_args = argv if request.cli_args is None else request.cli_args

    ns = parser.parse_args(cli_args[1:])

    if ns.help:
        request.writer.write(parser.format_help())
        return 0

    if ns.version:
        host_version = f"{request.host.name}/{request.host.version}"
        request.writer.write(f"{host_version} smokestack/{get_version()}\n")
        return 0

    if not ns.stack or ns.stack not in request.stacks:
        keys = ",".join(request.stacks.keys())
        request.writer.write(f'🔥 "--stack {{{keys}}}" is required\n')
        return 1

    stack = request.stacks[ns.stack](session=Session(), writer=request.writer)

    try:
        with stack.create_change_set() as change:
            if ns.preview:
                change.preview()
            if ns.deploy:
                change.execute()

    except SmokestackException as ex:
        request.writer.write(f"🔥 {str(ex)}\n")
        return 2

    return 0


def invoke_then_exit(request: Request) -> None:
    """Invokes `request` then exits with the appropriate shell code."""

    exit(invoke(request))
