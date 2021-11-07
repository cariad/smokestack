from typing import Dict, Literal, Sequence

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

Parameters = Dict[str, str]
