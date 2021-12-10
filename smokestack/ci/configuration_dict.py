from typing import List, TypedDict

from smokestack.ci.rule_dict import RuleDict


class ConfigurationDict(TypedDict):
    branch_name_env: str
    default: RuleDict
    rules: List[RuleDict]
