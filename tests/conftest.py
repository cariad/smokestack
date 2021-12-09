from mock import Mock
from pytest import fixture

from smokestack.types import ChangeSetArguments


@fixture
def session() -> Mock:
    return Mock()


@fixture
def change_set_args(session: Mock) -> ChangeSetArguments:
    return ChangeSetArguments(
        capabilities=[],
        body="",
        change_type="CREATE",
        parameters=[],
        session=session,
        stack="",
    )
