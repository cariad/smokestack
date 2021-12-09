from abc import abstractmethod
from io import StringIO
from pathlib import Path
from typing import List, Optional, Type, Union

from boto3.session import Session
from cfp import StackParameters

from smokestack.change_set import ChangeSet
from smokestack.protocols import StackProtocol
from smokestack.types import Capabilities, ChangeSetArguments


class Stack(StackProtocol):
    """
    An Amazon Web Services CloudFormation stack.
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        self._session = session or Session(region_name=self.region)
        self._stack_parameters: Optional[StackParameters] = None

        # A reference to "out" will be passed to the thread that creates and
        # operates on the change set. By anchoring the writer here, we'll have a
        # reference in the main thread that we can print to stdout later.
        self._out = StringIO()
        """
        String writer for anything to be considered as standard output.
        """

    @property
    def _resolved_body(self) -> str:
        """Gets the template body."""

        if isinstance(self.body, str):
            return self.body

        with open(self.body, "r") as f:
            return f.read()

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

    def change_set(self) -> ChangeSet:
        """Creates and returns a change set."""

        self._stack_parameters = StackParameters()
        self.parameters(self._stack_parameters)

        args = ChangeSetArguments(
            capabilities=self.capabilities,
            body=self._resolved_body,
            change_type="UPDATE" if self.exists else "CREATE",
            out=self._out,
            parameters=self._stack_parameters.api_parameters,
            session=self._session,
            stack=self.name,
        )

        return ChangeSet(args)

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

    @property
    def out(self) -> StringIO:
        """
        Gets a stream of any string to be considered as standard output.
        """

        return self._out

    def parameters(self, params: StackParameters) -> None:
        """
        Adds any stack parameters.

        No parameters will be added by default. Override this method only if
        your stack has parameters.

        For example, to reference a parameter value in Systems Manager Parameter
        Store:

        .. code-block:: python

            from smokestack import Stack
            from smokestack.parameters import FromParameterStore, StackParameters

            class ApplicationStack(Stack):

                # ...

                def parameters(self, params: StackParameters) -> None:
                    sp.add("InstanceType", FromParameterStore("/App/InstanceType"))
        """

    @property
    @abstractmethod
    def region(self) -> str:
        """Gets the Amazon Web Services region to deploy this stack into."""
