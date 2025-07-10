from dataclasses import dataclass


@dataclass
class AppConfig:
    """Application configuration."""

    config_file: str = "PyProject.json"
    ui_file: str = "MainDialog.ui"
    default_columns: int = 5
    default_python_version: str = "3.13.2"
    window_title: str = "PyProject"
    window_size: tuple[int, int] = (1024, 720)

    @classmethod
    def from_file(cls, config_path: str) -> "AppConfig":
        """Load configuration from file."""
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
            return cls(**data)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return cls()
