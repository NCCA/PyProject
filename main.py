#!/usr/bin/env -S uv run --script
import json
import logging
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QFile, Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QMainWindow,
    QPlainTextEdit,
    QProgressDialog,
    QWidget,
)

from AppConfig import AppConfig
from CommandGenerator import CommandGenerator
from Package import Package, PackageStatus
from ProjectManager import ProjectManager
from ProjectTemplate import ProjectTemplate
from PySide6.QtGui import QIcon
from Logger import logger
import resources_rc  # noqa: F401 qt resource


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, config: Optional[AppConfig] = None) -> None:
        """Initialize the MainWindow with UI setup and configuration loading."""
        super().__init__()
        # logger.error(QDir(":/").entryList(["*"], QDir.Files | QDir.NoSymLinks, QDir.Name))
        self.logger = logging.getLogger(__name__)
        self.config = config or AppConfig()

        # Initialize state
        self._project_location: Optional[str] = None
        self.template_data: Dict[str, Any] = {}
        self.uv_output: Optional[QPlainTextEdit] = None

        # Setup UI and tools
        self._setup_window()
        self._find_tools()
        self._setup_managers()
        self.load_ui()
        self.load_json_config(self.config.config_file)
        self._get_python_versions()
        self._connect_buttons()

    def _setup_window(self) -> None:
        """Setup basic window properties."""
        self.setWindowTitle(self.config.window_title)
        self.resize(*self.config.window_size)

    def _find_tools(self) -> None:
        """Find and store paths to uv and uvx executables."""
        self.uv_executable = shutil.which("uv")
        self.uvx_executable = shutil.which("uvx")

        if not self.uv_executable:
            self.logger.error("UV executable not found. Please install UV.")
            raise RuntimeError("UV executable not found")

        self.logger.info(f"Found uv: {self.uv_executable}")
        self.logger.info(f"Found uvx: {self.uvx_executable}")

    def _setup_managers(self) -> None:
        """Initialize manager classes."""
        self.command_generator = CommandGenerator(self.uv_executable)
        self.project_manager = ProjectManager(self.command_generator)

    @property
    def project_location(self) -> Optional[str]:
        """Get the current project location."""
        return self._project_location

    @project_location.setter
    def project_location(self, value: str) -> None:
        """Set the project location and update UI state."""
        self._project_location = value
        self._set_buttons_enabled(bool(value))

    @property
    def is_project_active(self) -> bool:
        """Check if a project location is set."""
        return self._project_location is not None

    def _set_buttons_enabled(self, enabled: bool) -> None:
        """Enable or disable project-related buttons."""
        if hasattr(self, "dry_run"):
            self.dry_run.setEnabled(enabled)
        if hasattr(self, "create_project"):
            self.create_project.setEnabled(enabled)
        if hasattr(self, "save_script"):
            self.save_script.setEnabled(enabled)
        if hasattr(self, "simple_script"):
            self.simple_script.setEnabled(enabled)

    def _get_python_versions(self) -> None:
        """
        Fetch available Python versions using uv and populate the version combo box.
        """
        try:
            result = subprocess.run(
                [self.uv_executable, "python", "list", "--output-format", "json"],
                capture_output=True,
                text=True,
                check=True,
            )
            versions = json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error fetching Python versions: {e}")
            return

        for idx, version in enumerate(versions):
            text = f"{version['version']} , {version['implementation']}"
            self.which_python.addItem(text)
            # Default to specified version if it exists
            if self.config.default_python_version in text:
                self.which_python.setCurrentIndex(idx)

    # def load_json_config(self, json_path: str) -> None:
    #     """
    #     Load project template configurations from a JSON file and setup UI.
    #     """
    #     try:
    #         with open(json_path, "r", encoding="utf-8") as f:
    #             raw_data = json.load(f)

    #         self.template_data = self._parse_template_data(raw_data)
    #         self._populate_template_combo()
    #         self._setup_current_template(0)
    #         self._set_buttons_enabled(False)

    #     except FileNotFoundError:
    #         self.logger.error(f"Configuration file not found: {json_path}")
    #         raise
    #     except json.JSONDecodeError as e:
    #         self.logger.error(f"Invalid JSON in configuration file: {e}")
    #         raise
    def load_json_config(self, json_path: str) -> None:
        """
        Load project template configurations from a JSON file (including Qt Resource) and setup UI.
        """
        from PySide6.QtCore import QFile, QIODevice, QTextStream
        import json

        try:
            file = QFile(json_path)
            if not file.open(QIODevice.ReadOnly | QIODevice.Text):
                raise IOError(f"Could not open {json_path}")

            stream = QTextStream(file)
            data = stream.readAll()
            file.close()

            raw_data = json.loads(data)
            self.template_data = self._parse_template_data(raw_data)
            self._populate_template_combo()
            self._setup_current_template(0)
            self._set_buttons_enabled(False)
        except Exception as e:
            # Handle error (log, show message, etc.)
            print(f"Failed to load config: {e}")

    def _parse_template_data(
        self, raw_data: Dict[str, Any]
    ) -> Dict[str, ProjectTemplate]:
        """Parse raw JSON data into ProjectTemplate objects."""
        templates = {}
        for name, data in raw_data.items():
            packages = [
                Package(pkg[0], pkg[1], pkg[2] if len(pkg) > 2 else None)
                for pkg in data.get("packages", [])
            ]
            templates[name] = ProjectTemplate(
                name=name,
                packages=packages,
                description=data.get("description", []),
                extras=data.get("extras", {}),
                pyproject_extras=data.get("pyproject_extras"),
            )
        return templates

    def _populate_template_combo(self) -> None:
        """Populate the template choice combo box."""
        if hasattr(self, "template_choice"):
            for template_name in self.template_data.keys():
                self.template_choice.addItem(template_name)

    def _connect_buttons(self) -> None:
        """Connect UI buttons to their respective handler methods."""
        self.select_location.clicked.connect(self._select_location)
        self.dry_run.clicked.connect(self._dry_run)
        self.save_script.clicked.connect(self._save_script)
        self.simple_script.clicked.connect(self._create_simple_script)
        self.create_project.clicked.connect(self._create_project)
        self.template_choice.currentIndexChanged.connect(self._setup_current_template)

    def _create_project(self) -> None:
        """Create the project in the selected location."""
        if not self.is_project_active:
            self.logger.warning("No project location selected.")
            return

        enabled_packages = self._get_enabled_packages()
        project_config = self._get_project_config()

        # Create progress dialog
        progress = QProgressDialog("Creating project...", "Cancel", 0, 100, self)
        progress.setWindowTitle("Progress")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        def progress_callback(step: int, message: str):
            self.uv_output.append(message)
            progress.setValue(step)
            QApplication.processEvents()
            return not progress.wasCanceled()

        success = self.project_manager.create_project(
            project_config, enabled_packages, progress_callback
        )

        progress.close()

        if success:
            self.uv_output.append("Project created successfully!\n\n")
            self._make_main_runnable(project_config["project_path"])
        else:
            self.uv_output.append("Project creation failed.\n\n")

    def _get_project_config(self) -> Dict[str, Any]:
        """Get the current project configuration."""
        project_path = Path(self.project_location) / self.project_name.text()
        python_version = self._get_selected_python_version()

        return {
            "project_path": project_path,
            "project_name": self.project_name.text(),
            "python_version": python_version,
        }

    def _get_selected_python_version(self) -> str:
        """Get the selected Python version."""
        return self.which_python.currentText().split(",")[0].strip()

    def _get_enabled_packages(self) -> List[Package]:
        """Get all enabled packages from the UI checkboxes."""
        return [
            Package(
                name=cb.objectName(),
                status=PackageStatus.ENABLED.value,
                version=cb.property("version"),
            )
            for cb in self._get_package_checkboxes()
            if cb.isChecked()
        ]

    def _get_package_checkboxes(self) -> List[QCheckBox]:
        """Get all package checkboxes from the options layout."""
        if not hasattr(self, "options_gb"):
            return []

        layout = self.options_gb.layout()
        return [
            layout.itemAt(i).widget()
            for i in range(layout.count())
            if isinstance(layout.itemAt(i).widget(), QCheckBox)
        ]

    def _make_main_runnable(self, project_path: Path) -> None:
        """Make the main.py file executable with proper shebang."""
        main_py = project_path / "main.py"
        if main_py.exists():
            self._make_script_executable(main_py)

    def _make_script_executable(self, file_path: Path) -> None:
        """Make a Python script executable with proper shebang."""
        file_path.chmod(file_path.stat().st_mode | stat.S_IEXEC)
        content = file_path.read_text()
        file_path.write_text(f"#!/usr/bin/env -S uv run --script\n{content}")

    def _save_script(self) -> None:
        """Save the generated script to a file."""
        # TODO: Implement script saving functionality
        self.logger.info("Save script functionality not yet implemented")

    def _dry_run(self) -> None:
        """Generate the commands to create the project but don't execute them."""
        if not self.is_project_active:
            self.logger.warning("No project location selected.")
            return

        enabled_packages = self._get_enabled_packages()
        project_config = self._get_project_config()
        commands = self.command_generator.generate_all_commands(
            project_config, enabled_packages
        )

        self.uv_output.append("Dry run - Commands that would be executed:\n")
        for cmd in commands:
            self.uv_output.append(f"  {cmd}")
        self.uv_output.append("\n")

    def _create_simple_script(self) -> None:
        """Create a simple executable Python script."""
        file_path = self._get_script_file_path()
        if not file_path:
            return

        python_version = self._get_selected_python_version()
        cmd = (
            f"{self.uv_executable} init --script --python {python_version} {file_path}"
        )

        try:
            subprocess.run(cmd, shell=True, check=True)
            self._make_script_executable(file_path)
            self.logger.info(f"Created executable script: {file_path}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error creating script: {e}")

    def _get_script_file_path(self) -> Optional[Path]:
        """Get the file path for script creation using dialog."""
        file_name = QFileDialog.getSaveFileName(
            self, "Save Python Script", "", "Python Files (*.py)"
        )[0]
        return Path(file_name) if file_name else None

    def _select_location(self) -> None:
        """Open a file dialog to select the project location."""
        options = QFileDialog.Options()
        directory = QFileDialog.getExistingDirectory(
            self, "Select Project Location", "", options=options
        )
        if directory:
            self.project_location.setText(directory)
            self.project_location = directory

    def _setup_current_template(self, index: int) -> None:
        """Setup the UI based on the selected template configuration."""
        if not hasattr(self, "template_choice") or self.template_choice.count() == 0:
            return

        self.template_choice.setCurrentIndex(index)
        template_name = self.template_choice.currentText()
        template = self.template_data.get(template_name)

        if not template:
            return

        # Update description
        self.description_text.clear()
        self.description_text.setPlainText("\n".join(template.description))

        # Generate options and extras
        self._generate_options(template)
        self._generate_extras(template)

    def _generate_options(self, template: ProjectTemplate) -> None:
        """Generate package option checkboxes based on template data."""
        if not hasattr(self, "options_gb"):
            return

        layout = self.options_gb.layout()
        self._clear_layout(layout)

        for idx, package in enumerate(template.packages):
            checkbox = QCheckBox()
            checkbox.setObjectName(package.name)
            checkbox.setText(package.name)
            checkbox.setChecked(package.is_enabled)

            if package.version:
                checkbox.setProperty("version", package.version)

            row = idx // self.config.default_columns
            col = idx % self.config.default_columns
            layout.addWidget(checkbox, row, col)

    def _generate_extras(self, template: ProjectTemplate) -> None:
        """Generate extra options based on template data."""
        if not hasattr(self, "extras_gb"):
            return

        layout = self.extras_gb.layout()
        self._clear_layout(layout)

        self._generate_template_checkboxes(template.extras, layout)
        self._generate_pyproject_extras(template.pyproject_extras, layout)

    def _generate_template_checkboxes(self, extras: Dict[str, Any], layout) -> None:
        """Generate checkboxes for template files."""
        templates = extras.get("templates", [])

        for i in range(0, len(templates), 3):
            if i + 2 < len(templates):
                checkbox = QCheckBox()
                checkbox.setText(templates[i + 2])
                checkbox.setProperty("src", templates[i])
                checkbox.setProperty("dst", templates[i + 1])
                checkbox.setObjectName(f"template_{i // 3}")
                checkbox.setChecked(True)

                row = i // (self.config.default_columns * 3)
                col = (i // 3) % self.config.default_columns
                layout.addWidget(checkbox, row, col)

    def _generate_pyproject_extras(
        self, pyproject_extras: Optional[List[str]], layout
    ) -> None:
        """Generate text edit for pyproject.toml extras."""
        if not pyproject_extras:
            return

        toml_text_edit = QPlainTextEdit()
        toml_text_edit.setPlainText("\n".join(pyproject_extras))
        layout.addWidget(toml_text_edit, 10, 0, 1, self.config.default_columns)

    def _clear_layout(self, layout) -> None:
        """Clear all widgets from a layout."""
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

    def load_ui(self) -> None:
        """Load the UI from a .ui file and set up the connections."""
        try:
            loader = QUiLoader()
            ui_file = QFile(self.config.ui_file)
            ui_file.open(QFile.ReadOnly)

            loaded_ui = loader.load(ui_file, self)
            self.setCentralWidget(loaded_ui)

            # Add all children with object names as attributes
            for child in loaded_ui.findChildren(QWidget):
                name = child.objectName()
                if name:
                    setattr(self, name, child)

            ui_file.close()

        except Exception as e:
            self.logger.error(f"Error loading UI file: {e}")
            raise

    def keyPressEvent(self, event) -> None:
        """Handle key press events."""
        if event.key() == Qt.Key_Escape:
            self.close()


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    # this needs to be loaded locally for menu bars etc as resources are not read by the system icon setup
    app.setWindowIcon(QIcon("pyproject.png"))

    try:
        config = AppConfig()
        window = MainWindow(config)
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
