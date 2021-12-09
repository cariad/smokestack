from typing import TypedDict

from smokestack.ci.ci_dict import CiDict


class ConfigurationDict(TypedDict):
    branch_name_env: str
    ci: CiDict
