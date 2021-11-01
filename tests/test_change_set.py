from pytest import mark

from smokestack.change_set import ChangeSet, ChangeSetArgs
from smokestack.types import ChangeType


@mark.parametrize(
    "change_type, expect",
    [
        ("UPDATE", "stack_update_complete"),
        ("CREATE", "stack_create_complete"),
    ],
)
def test_stack_waiter_type(
    change_set_args: ChangeSetArgs,
    change_type: ChangeType,
    expect: str,
) -> None:
    change_set_args["change_type"] = change_type
    assert ChangeSet(change_set_args).stack_waiter_type == expect
