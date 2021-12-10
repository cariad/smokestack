from pathlib import Path

from smokestack.exceptions.smokestack import SmokestackError


class ConfigurationError(SmokestackError):
    def __init__(self, path: Path, reason: str) -> None:
        abs_path = path.resolve().absolute().as_posix()
        super().__init__(f"Invalid configuration at {abs_path}: {reason}")
