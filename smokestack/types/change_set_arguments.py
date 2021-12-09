from dataclasses import dataclass, field
from typing import List

from boto3.session import Session
from cfp import ApiParameter

from smokestack.types.capability import Capabilities
from smokestack.types.change_type import ChangeType


@dataclass
class ChangeSetArguments:
    body: str
    change_type: ChangeType
    session: Session
    stack: str
    capabilities: Capabilities = field(default_factory=list)
    parameters: List[ApiParameter] = field(default_factory=list)
