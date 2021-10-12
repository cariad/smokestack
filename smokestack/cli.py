from argparse import ArgumentParser
from sys import argv, stdout
from typing import IO, Dict, List, Type

from boto3.session import Session

from smokestack.exceptions import SmokestackException
from smokestack.stack import Stack
from smokestack.version import get_version


def invoke(
    name: str,
    version: str,
    stacks: Dict[str, Type[Stack]],
    args: List[str] = argv,
    writer: IO[str] = stdout,
) -> int:
    """
    Invokes the command line arguments `args` for the relevant stack in `stacks`
    and writes any responses to `writer`.

    Returns the shell exit code.
    """

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
        choices=stacks.keys(),
        help="stack",
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="prints version",
    )

    ns = parser.parse_args(args[1:])

    if ns.help:
        writer.write(parser.format_help())
        return 0

    if ns.version:
        writer.write(f"{name}/{version} smokestack/{get_version()}\n")
        return 0

    if not ns.stack or ns.stack not in stacks:
        writer.write(f'🔥 "--stack {{{",".join(stacks.keys())}}}" is required\n')
        return 1

    stack = stacks[ns.stack](session=Session(), writer=writer)

    try:

        with stack.create_change_set() as change:
            if ns.preview:
                change.preview()
            if ns.deploy:
                change.execute()

    except SmokestackException as ex:
        writer.write(f"🔥 {str(ex)}\n")
        return 2

    return 0
