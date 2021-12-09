from enum import Enum, unique


@unique
class StackStatus(Enum):
    IN_PROGRESS = "in progress"
    QUEUED = "queued"
    DONE = "done"
    READY = "ready"
