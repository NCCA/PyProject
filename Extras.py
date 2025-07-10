from dataclasses import dataclass
from enum import Enum


class ExtrasStatus(Enum):
    """Enum for package status."""

    ENABLED = "enabled"
    DISABLED = "disabled"


@dataclass
class Extras:
    """Represents the extra files to be copied from template dirs"""

    src: str
    dst: str
    status: ExtrasStatus = ExtrasStatus.DISABLED

    @property
    def is_enabled(self) -> bool:
        """Check if the package is enabled."""
        return self.status == ExtrasStatus.ENABLED.value
