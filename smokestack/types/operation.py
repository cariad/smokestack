from dataclasses import dataclass


@dataclass
class Operation:
    execute: bool = False
    preview: bool = False
