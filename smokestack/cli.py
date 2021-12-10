from argparse import ArgumentParser
from typing import List, Type

from cline import AnyTask, ArgumentParserCli

import smokestack.tasks


class SmokestackCli(ArgumentParserCli):
    def make_parser(self) -> ArgumentParser:
        """
        Gets the argument parser.
        """

        parser = ArgumentParser(
            description="Deploys CloudFormation stacks, beautifully.",
            epilog="Made with love by Cariad Eccleston: https://github.com/cariad/smokestack",
        )

        parser.add_argument("set", help="Stack set", nargs="?")

        parser.add_argument(
            "--ci",
            action="store_true",
            help='run configuration in "smokestack-ci.yml"',
        )

        parser.add_argument(
            "--execute",
            action="store_true",
            help="execute any changes",
        )

        parser.add_argument(
            "--preview",
            action="store_true",
            help="preview any changes",
        )

        parser.add_argument(
            "--version",
            action="store_true",
            help="prints version",
        )

        parser.add_argument(
            "--log-level",
            help="log level",
            metavar="LEVEL",
            default="CRITICAL",
        )

        return parser

    def register_tasks(self) -> List[Type[AnyTask]]:
        """
        Gets the tasks that this CLI can perform.
        """

        return [
            smokestack.tasks.OperateTask,
        ]
