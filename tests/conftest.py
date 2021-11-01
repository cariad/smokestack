from io import StringIO

from mock import Mock
from pytest import fixture

from smokestack.change_set import ChangeSetArgs


@fixture
def session() -> Mock:
    return Mock()


@fixture
def writer() -> StringIO:
    return StringIO()


@fixture
def change_set_args(session: Mock, writer: StringIO) -> ChangeSetArgs:
    return {
        "capabilities": [],
        "body": "",
        "change_type": "CREATE",
        "session": session,
        "stack_name": "",
        "writer": writer,
    }
