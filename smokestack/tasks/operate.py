from dataclasses import dataclass
from logging import getLogger

from cline import CannotMakeArguments, CommandLineArguments, Task

from smokestack.ci import get_operation
from smokestack.exceptions import SmokestackError
from smokestack.register import get_registered_stack_set
from smokestack.types import Operation


@dataclass
class OperateTaskArguments:
    operation: Operation
    stack_set: str
    log_level: str = "CRITICAL"


class OperateTask(Task[OperateTaskArguments]):
    def invoke(self) -> int:
        getLogger("smokestack").setLevel(self.args.log_level)

        stack_set_type = get_registered_stack_set(self.args.stack_set)
        stack_set = stack_set_type(out=self.out)

        try:
            stack_set.execute(self.args.operation)

        except SmokestackError as ex:
            self.out.write("\n🔥 ")
            self.out.write(str(ex))
            self.out.write("\n\n")
            return 1

        return 0

    @classmethod
    def make_args(cls, args: CommandLineArguments) -> OperateTaskArguments:
        ci = args.get_bool("ci", False)
        execute = args.get_bool("execute", False)
        preview = args.get_bool("preview", False)

        if ci and (execute or preview):
            raise CannotMakeArguments("CI must be the only operation.")

        op = get_operation() if ci else Operation(execute=execute, preview=preview)

        if not (op.execute or op.preview):
            raise CannotMakeArguments("Must execute and/or preview.")

        return OperateTaskArguments(
            log_level=args.get_string("log_level", "CRITICAL").upper(),
            operation=op,
            stack_set=args.get_string("set"),
        )
