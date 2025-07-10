from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from Package import Package


@dataclass
class ProjectTemplate:
    """Represents a project template configuration."""

    name: str
    packages: List[Package]
    description: List[str]
    extras: Dict[str, Any]
    pyproject_extras: Optional[List[str]] = None
