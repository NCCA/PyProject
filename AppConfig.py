from dataclasses import dataclass
import resources_rc  # noqa: F401 qt resource


@dataclass
class AppConfig:
    """Application configuration."""

    config_file: str = ":/templates/PyProject.json"
    ui_file: str = ":/ui/MainDialog.ui"
    default_columns: int = 5
    default_python_version: str = "3.13.2"
    window_title: str = "PyProject"
    window_size: tuple[int, int] = (1024, 720)
