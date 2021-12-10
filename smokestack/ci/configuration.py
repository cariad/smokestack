from logging import getLogger
from os import environ
from pathlib import Path
from typing import Optional, cast

from yaml import safe_load

from smokestack.ci.configuration_dict import ConfigurationDict
from smokestack.ci.operation_dict import OperationDict
from smokestack.exceptions import ConfigurationError
from smokestack.types import Operation

logger = getLogger("smokestack")
default_path = Path().resolve().absolute() / "smokestack-ci.yml"


def load(path: Optional[Path] = None) -> ConfigurationDict:
    path = path or default_path

    logger.debug("Loading CI configuration: %s", default_path.as_posix())

    try:
        with open(path, "r") as f:
            return cast(ConfigurationDict, safe_load(f))

    except FileNotFoundError:
        raise ConfigurationError(path, "File not found.")


def get_operation_dict(branch: str, config: ConfigurationDict) -> OperationDict:
    for rule in config["rules"]:
        if rule.get("branch", None) == branch:
            return rule

    logger.warning("No CI rule for branch: %s", branch)
    return config["default"]


def get_operation() -> Operation:
    config = load()

    branch = environ.get(config["branch_name_env"], None)
    if branch is None:
        raise ConfigurationError(
            default_path,
            f'No branch name: {config["branch_name_env"]}',
        )

    op_dict = get_operation_dict(branch, config)
    return Operation(**op_dict)
