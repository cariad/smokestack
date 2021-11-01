from typing import TypedDict


class OperationValues(TypedDict):
    deploy: bool
    preview: bool


class Operation:
    def __init__(self, values: OperationValues) -> None:
        self._values = values

    @property
    def deploy(self) -> bool:
        return self._values["deploy"]

    @property
    def preview(self) -> bool:
        return self._values["preview"]
