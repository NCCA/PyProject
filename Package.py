from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PackageStatus(Enum):
    """Enum for package status."""

    ENABLED = "enabled"
    DISABLED = "disabled"


@dataclass
class Package:
    """Represents a Python package with its configuration."""

    name: str
    status: str
    version: Optional[str] = None

    @property
    def is_enabled(self) -> bool:
        """Check if the package is enabled."""
        return self.status == PackageStatus.ENABLED.value

    @property
    def version_spec(self) -> str:
        """Get the package specification with version."""
        return f"{self.name}{self.version}" if self.version else self.name
