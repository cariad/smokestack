from typing import List, TypedDict

from smokestack.ci.rule_dict import RuleDict


class CiDict(TypedDict):
    default: RuleDict
    rules: List[RuleDict]
