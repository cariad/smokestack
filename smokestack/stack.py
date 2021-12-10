from abc import abstractmethod
from io import StringIO
from logging import getLogger
from pathlib import Path
from typing import List, Optional, Type, Union

from ansiscape import heavy, yellow
from ansiscape.checks import should_emit_codes
from boto3.session import Session
from cfp import StackParameters

from smokestack.change_set import ChangeSet
from smokestack.protocols import StackProtocol
from smokestack.types import Capabilities


class Stack(StackProtocol):
    """
    An Amazon Web Services CloudFormation stack.
    """

    def __init__(self, session: Optional[Session] = None) -> None:

        self._logger = getLogger("smokestack")

        # # A reference to "out" will be passed to the thread that creates and
        # # operates on the change set. By anchoring the writer here, we'll have a
        # # reference in the main thread that we can print to stdout later.
        # self._out = StringIO()
        # """
        # String writer for anything to be considered as standard output.
        # """

        self._session = session or Session(region_name=self.region)
        self._stack_parameters = StackParameters()

        self._logger.debug("Initialised %s.", self.__class__.__name__)

    @property
    @abstractmethod
    def body(self) -> Union[str, Path]:
        """
        Gets the template body or path to the template file.
        """

    @property
    def capabilities(self) -> Capabilities:
        """
        Gets the capabilities required to deploy this stack.

        Returns no capabilities by default.
        """

        return []

    def change_set(self, out: StringIO) -> ChangeSet:
        """Creates and returns a change set."""

        name = yellow(self.name) if should_emit_codes else self.name
        region = yellow(self.region) if should_emit_codes else self.region
        line = f"🌞 Stack {name} in {region}"
        line_fmt = heavy(line).encoded if should_emit_codes else line
        out.write(line_fmt)
        out.write("\n")

        self._logger.debug("Populating parameters...")
        self.parameters(self.stack_parameters)

        if self._stack_parameters.api_parameters:
            heading = "Parameters:"
            heading_fmt = heavy(heading) if should_emit_codes else heading
            out.write(f"\n{heading_fmt}\n")
            self._stack_parameters.render(out)

        return ChangeSet(stack=self, out=out)

    @property
    def exists(self) -> bool:
        """Returns `True` if the stack exists, otherwise `False`."""

        # pyright: reportUnknownMemberType=false
        self.client = self._session.client("cloudformation")

        try:
            self.client.describe_stacks(StackName=self.name)
            return True
        except self.client.exceptions.ClientError:
            return False

    @property
    @abstractmethod
    def name(self) -> str:
        """Gets the stack's name."""

    @property
    def needs(self) -> List[Type["Stack"]]:
        """
        Gets the stacks that must be deployed before this one.

        The stack has no dependencies by default. Override this property only if
        you have dependencies to describe.

        In this example, Smokestack will ensure that the database and logging
        stacks are deployed before deploying the application stack:

        .. code-block:: python

            from smokestack import Stack

            import myproject.stacks


            class ApplicationStack(Stack):

                # ...

                @property
                def needs(self) -> List[Type[Stack]]:
                    return [
                        myproject.stacks.DatabaseStack,
                        myproject.stacks.LoggingStack,
                    ]
        """

        return []

    # @property
    # def out(self) -> StringIO:
    #     """
    #     Gets a stream of any string to be considered as standard output.
    #     """

    #     return self._out

    def parameters(self, params: StackParameters) -> None:
        """
        Gets stack parameters
        """

        return None

    @property
    @abstractmethod
    def region(self) -> str:
        """Gets the Amazon Web Services region to deploy this stack into."""

    @property
    def session(self) -> Session:
        """Gets this stack's Boto3 session."""

        return self._session

    @property
    def stack_parameters(self) -> StackParameters:
        return self._stack_parameters
