from pathlib import Path
from typing import Any, Dict, List

from Package import Package


class CommandGenerator:
    """Handles generation of UV commands for project creation."""

    def __init__(self, uv_executable: str):
        self.uv_executable = uv_executable

    def generate_init_command(self, project_path: Path, project_name: str, python_version: str) -> str:
        """Generate the project initialization command."""
        return f"{self.uv_executable} init --python {python_version} --name {project_name} {project_path}"

    def generate_add_command(self, package: Package, project_path: Path) -> str:
        """Generate a package addition command."""
        if package.version:
            return f"{self.uv_executable} add '{package.version_spec}' --project {project_path}"
        return f"{self.uv_executable} add {package.name} --project {project_path}"

    def generate_all_commands(self, project_config: Dict[str, Any], enabled_packages: List[Package]) -> List[str]:
        """Generate all commands needed to create the project."""
        commands = []

        # Add init command
        init_cmd = self.generate_init_command(
            project_config["project_path"], project_config["project_name"], project_config["python_version"]
        )
        commands.append(init_cmd)

        # Add package commands
        for package in enabled_packages:
            if package.is_enabled:
                cmd = self.generate_add_command(package, project_config["project_path"])
                commands.append(cmd)

        return commands
