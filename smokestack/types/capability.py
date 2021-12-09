from typing import Literal, Sequence

Capability = Literal[
    "CAPABILITY_AUTO_EXPAND",
    "CAPABILITY_IAM",
    "CAPABILITY_NAMED_IAM",
]

Capabilities = Sequence[Capability]
