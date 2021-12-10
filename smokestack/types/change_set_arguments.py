# from dataclasses import dataclass, field
# from io import StringIO
# from typing import List

# from boto3.session import Session
# from cfp import ApiParameter

# from smokestack.types.capability import Capabilities
# from smokestack.types.change_type import ChangeType


# @dataclass
# class ChangeSetArguments:
#     body: str
#     change_type: ChangeType

#     # "out" needs to be passed into the change set (as opposed to created and
#     # owned by the change set) because it could end up holding the rendered
#     # event stack if the operation fails. We need to hold onto that render
#     # longer than the change set will live.
#     out: StringIO
#     """
#     String writer for anything to be considered as standard output.
#     """

#     session: Session
#     stack: str
#     capabilities: Capabilities = field(default_factory=list)
#     parameters: List[ApiParameter] = field(default_factory=list)
