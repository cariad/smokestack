from dataclasses import dataclass


@dataclass
class Host:
    """Information about the host application."""

    name: str
    """Host application name."""

    version: str
    """Host application version."""
