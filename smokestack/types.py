from typing import Literal, Sequence

ChangeType = Literal[
    "CREATE",
    "IMPORT",
    "UPDATE",
]

Capability = Literal[
    "CAPABILITY_AUTO_EXPAND",
    "CAPABILITY_IAM",
    "CAPABILITY_NAMED_IAM",
]

Capabilities = Sequence[Capability]
