import logging
import subprocess
from typing import Any, Dict, List

from CommandGenerator import CommandGenerator
from Package import Package

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProjectManager:
    """Manages project creation and configuration."""

    def __init__(self, command_generator: CommandGenerator):
        self.command_generator = command_generator
        self.logger = logging.getLogger(__name__)

    def create_project(
        self, project_config: Dict[str, Any], enabled_packages: List[Package], progress_callback=None
    ) -> bool:
        """Create a project with the given configuration."""
        commands = self.command_generator.generate_all_commands(project_config, enabled_packages)

        for idx, cmd in enumerate(commands):
            if progress_callback:
                progress_callback(idx, f"Executing: {cmd}")

            try:
                result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
                if progress_callback:
                    progress_callback(idx, result.stdout)
                    if result.stderr:
                        progress_callback(idx, result.stderr)
            except subprocess.CalledProcessError as e:
                error_msg = f"Error executing command: {e}"
                self.logger.error(error_msg)
                if progress_callback:
                    progress_callback(idx, error_msg)
                    if e.stdout:
                        progress_callback(idx, e.stdout)
                    if e.stderr:
                        progress_callback(idx, e.stderr)
                return False

        return True
