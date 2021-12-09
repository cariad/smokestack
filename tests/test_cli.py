from smokestack.cli import SmokestackCli
from smokestack.tasks import OperateTask

def test() -> None:
    cli = SmokestackCli(args=["foo", "--preview"])
    assert isinstance(cli.task, OperateTask)
