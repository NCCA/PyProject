from pathlib import Path
from typing import Any, Dict, List

from Extras import Extras
from Package import Package


class CommandGenerator:
    """Handles generation of UV commands for project creation."""

    def __init__(self, uv_executable: str):
        self.uv_executable = uv_executable

    def generate_init_command(self, project_config) -> str:
        """Generate the project initialization command."""
        return (
            f"{self.uv_executable} init {project_config['gen_type']} "
            f"--python {project_config['python_version']} "
            f"--name {project_config['project_name']} "
            f"{project_config['vcs_option']} "
            f"{project_config['no_readme']} "
            f"{project_config['no_workspace']} "
            f"{project_config['project_path']}"
        )

    def generate_add_command(self, package: Package, project_path: Path) -> str:
        """Generate a package addition command."""
        if package.version:
            return f"{self.uv_executable} add '{package.version_spec}' --project {project_path}"
        return f"{self.uv_executable} add {package.name} --project {project_path}"

    def generate_extra_command(self, extra: Extras, project_path: Path) -> str:
        """Generate a package addition command."""
        return f"cp templates/{extra.src} {project_path}/{extra.dst}"

    def generate_all_commands(
        self,
        project_config: Dict[str, Any],
        enabled_packages: List[Package],
        extras: List[Extras],
    ) -> List[str]:
        """Generate all commands needed to create the project."""
        commands = []

        # Add init command
        init_cmd = self.generate_init_command(project_config)
        commands.append(init_cmd)

        # Add package commands
        for package in enabled_packages:
            if package.is_enabled:
                cmd = self.generate_add_command(package, project_config["project_path"])
                commands.append(cmd)
        # Add package commands
        for extra in extras:
            if extra.is_enabled:
                cmd = self.generate_extra_command(extra, project_config["project_path"])
                commands.append(cmd)

        return commands
