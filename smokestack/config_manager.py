from os import environ
from pathlib import Path
from typing import IO, List, Optional, TypedDict

from ansiscape import yellow
from yaml import safe_load

from smokestack.exceptions import SmokestackError
from smokestack.models import OperationValues


class CiRuleConfigurationValues(OperationValues):
    branch: str


class CiConfigurationValues(TypedDict):
    default: CiRuleConfigurationValues
    rules: List[CiRuleConfigurationValues]


class ConfigurationValues(TypedDict):
    branch_name_env: str
    ci: CiConfigurationValues


class ConfigurationError(SmokestackError):
    def __init__(self, reason: str) -> None:
        path = Configuration.path()
        super().__init__(f"Invalid configuration at {path}: {reason}")


class MissingConfigurationError(ConfigurationError):
    def __init__(self, key: str) -> None:
        super().__init__(f'missing or empty key "{key}"')


class Configuration:
    _values: ConfigurationValues

    @classmethod
    def branch(cls) -> Optional[str]:
        return environ.get(cls.branch_name_env(), None)

    @classmethod
    def branch_name_env(cls) -> str:
        env_name = cls._values.get("branch_name_env", None)
        if not env_name:
            raise MissingConfigurationError("branch_name_env")
        return env_name

    @classmethod
    def load(cls) -> None:
        try:
            with open(cls.path(), "r") as f:
                cls._values = safe_load(f)
        except FileNotFoundError:
            raise ConfigurationError("file not found")

    @classmethod
    def operation(cls, writer: IO[str]) -> OperationValues:
        ci = cls._values["ci"]
        rules = ci["rules"]
        branch = cls.branch()
        if not branch:
            raise ConfigurationError(
                f'environment variable "{cls.branch_name_env()}" does not describe a branch'
            )

        for rule in rules:
            if rule.get("branch", None) == branch:
                writer.write(f"Found a rule for branch {yellow(branch).encoded}!\n")
                return rule

        writer.write(
            f"Did not find a rule for branch {yellow(branch).encoded} so using default rule.\n"
        )
        return ci["default"]

    @classmethod
    def path(cls) -> Path:
        return Path().resolve().absolute() / "smokestack.yml"


def make_operation_from_config(writer: IO[str]) -> OperationValues:
    return Configuration.operation(writer)
