#!/usr/bin/env -S uv run --script

#!/usr/bin/env -S uv run --script

import json
import shutil
import stat
import subprocess
import sys
from pathlib import Path

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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyProject")
        self.resize(1024, 720)
        self.load_ui()
        self.load_json_config("PyProject.json")
        self._find_tools()
        self._get_python_versions()
        self._connect_buttons()
        self.project_active = False

    def _find_tools(self) -> None:
        self.uv_executable = shutil.which("uv")
        self.uvx_executable = shutil.which("uvx")
        print(f"{self.uv_executable=}")
        print(f"{self.uvx_executable=}")

    def _get_python_versions(self):
        """
        uv python list --output-format json will give us the data we need but we only the numbers
        """
        import subprocess

        try:
            result = subprocess.run(
                [self.uv_executable, "python", "list", "--output-format", "json"],
                capture_output=True,
                text=True,
                check=True,
            )
            versions = json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error fetching Python versions: {e}")
            return []

        # print([version["version"] for version in versions])
        for idx, version in enumerate(versions):
            installed = " (installed)" if version["path"] else ""
            text = f"{version['version']} , {version['implementation']} {installed}"
            self.which_python.addItem(text)
            # default to python 3.13.3 if it exists
            if "3.13.2" in text:
                self.which_python.setCurrentIndex(idx)

    def load_json_config(self, json_path: str) -> None:
        """
        Load applications from a JSON file and setup ui

        Args:
            json_path: Path to the JSON file.
        """
        with open(json_path, "r", encoding="utf-8") as f:
            self.template_data = json.load(f)
        print(self.template_data)

        # now populate the combo box with the keys from the JSON data
        for key in self.template_data.keys():
            # Assuming you have a combo box named `comboBox`
            if hasattr(self, "template_choice"):
                self.template_choice.addItem(key)
            self._setup_current_template(0)

        # Default disable buttons until we have a project location
        self.dry_run.setEnabled(False)
        self.create_project.setEnabled(False)
        self.save_script.setEnabled(False)
        self.save_script.setEnabled(False)

    def _connect_buttons(self) -> None:
        self.select_location.clicked.connect(self._select_location)
        self.dry_run.clicked.connect(self._dry_run)
        self.save_script.clicked.connect(self._save_script)
        self.simple_script.clicked.connect(self._create_simple_script)
        self.create_project.clicked.connect(self._create_project)
        self.template_choice.currentIndexChanged.connect(lambda index: self._setup_current_template(index))

    def _create_project(self) -> None:
        """
        This will create the project in the selected location.
        """
        if not self.project_active:
            print("No project location selected.")
            return

        commands = self._generate_uv_commands()
        if not commands:
            print("No commands generated. Please check your configuration.")
            return

        # Show a progress dialog while executing the commands
        progress = QProgressDialog("Running commands...", "Cancel", 0, len(commands), self)
        progress.setWindowTitle("Progress")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        # Execute the commands
        for idx, cmd in enumerate(commands):
            self.uv_output.append(f"Executing: {cmd}")
            progress.setValue(idx)
            QApplication.processEvents()
            if progress.wasCanceled():
                self.uv_output.append("Operation canceled by user.\n")
                break
            try:
                result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
                self.uv_output.append(result.stdout)
                if result.stderr:
                    self.uv_output.append(result.stderr)
            except subprocess.CalledProcessError as e:
                self.uv_output.append(f"Error executing command: {e}\n")
                if e.stdout:
                    self.uv_output.append(e.stdout)
                if e.stderr:
                    self.uv_output.append(e.stderr)
            self.uv_output.update()
        self.uv_output.append("DONE\n\n")
        if self.make_runnable.isChecked() and self.app_type.currentIndex() == 0:
            self._make_runnable(self.project_location.text() + "/" + self.project_name.text() + "/main.py")
        progress.setValue(len(commands))

    def _save_script(self) -> None: ...

    def _dry_run(self) -> None:
        """
        This will generate the commands to create the project but not execute them.
        """
        if not self.project_active:
            print("No project location selected.")
            return

        commands = self._generate_uv_commands()
        # append the commands to the output text edit
        for cmd in commands:
            self.uv_output.append(cmd)

    def _create_simple_script(self) -> None:
        # grab a python file name using the dialog
        file_name = QFileDialog.getSaveFileName(self, "Save Python Script", "", "Python Files (*.py)")[0]
        if file_name:
            python_version = self.which_python.currentText().split(",")[0].strip()
            cmd = f"{self.uv_executable} init --script --python {python_version}  {file_name}"
            print(cmd)
            try:
                subprocess.run(cmd, shell=True, check=True)
                if self.make_runnable.isChecked():
                    self._make_runnable(file_name)

            except subprocess.CalledProcessError as e:
                print(f"Error executing command: {e}")

    def _make_runnable(self, file_name):
        exe_file = Path(file_name)
        exe_file.chmod(exe_file.stat().st_mode | stat.S_IEXEC)
        content = exe_file.read_text()
        exe_file.write_text(f"#!/usr/bin/env -S uv run --script\n{content}")

    def _generate_uv_commands(self) -> list[str]:
        commands = []
        generator = ["--app", "--package", "--lib"]
        gen_type = generator[self.app_type.currentIndex()]
        # first to create the project folder
        project_path = Path(self.project_location.text()) / self.project_name.text()
        python_version = self.which_python.currentText().split(",")[0].strip()
        vcs_option = "--vcs git" if self.use_git.isChecked() else "--vcs none"
        no_readme = "--no-readme" if self.no_readme.isChecked() else ""
        no_workspace = "--no-workspace" if self.no_workspace.isChecked() else ""
        cmd = f"{self.uv_executable} init {gen_type} --python {python_version} --name {self.project_name.text()} {vcs_option} {no_readme} {no_workspace} {project_path}"
        commands.append(cmd)
        # Now we will add the packages
        # we will iterate over the checkboxes in the options group box and add the ones that are checked
        options_layout = self.options_gb.layout()
        for i in range(options_layout.count()):
            checkbox = options_layout.itemAt(i).widget()
            if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                package_name = checkbox.objectName()
                # Check if the checkbox has a version property
                # if it does, we will add it to the command
                version = checkbox.property("version")
                if version:
                    cmd = f"{self.uv_executable} add '{package_name}{version}' --project {project_path}"
                else:
                    cmd = f"{self.uv_executable} add {package_name} --project {project_path}"
                commands.append(cmd)

        # Now we will add the extras
        extras_layout = self.extras_gb.layout()
        for i in range(extras_layout.count()):
            checkbox = extras_layout.itemAt(i).widget()
            if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                src = checkbox.property("src")
                dst = checkbox.property("dst")
                if src and dst:
                    cmd = f"cp templates/{src} {project_path}/{dst}"
                    commands.append(cmd)

        return commands

    def _select_location(self) -> None:
        """
        Open a file dialog to select the project location.
        """
        options = QFileDialog.Options()
        directory = QFileDialog.getExistingDirectory(self, "Select Project Location", "", options=options)
        if directory:
            self.project_location.setText(directory)
            self.project_active = True
            # enable the buttons
            self.dry_run.setEnabled(True)
            self.create_project.setEnabled(True)
            self.save_script.setEnabled(True)
            self.simple_script.setEnabled(True)

    def _setup_current_template(self, index: str) -> None:
        # we will now select the first item in the combo box and populate
        # the rest of the UI with the data from the JSON
        if hasattr(self, "template_choice") and self.template_choice.count() > 0:
            self.template_choice.setCurrentIndex(index)
            data = self.template_data[self.template_choice.currentText()]
        # we have desciption as an array of strings that needs to be \n seperated so add this to the QPlainTextEdit
        self.description_text.clear()
        self.description_text.setPlainText("\n".join(data.get("description", [])))
        # now add all the options to the options group_box
        self._generate_options(data)
        # now add the extras to the extras group box
        self._generate_extras(data)

    def _generate_options(self, data) -> None:
        options_layout = self.options_gb.layout()
        packages = data.get("packages", {})
        columns = 5
        # first remove all existing widgets in the layout
        for i in reversed(range(options_layout.count())):
            options_layout.itemAt(i).widget().deleteLater()

        for idx, package in enumerate(packages):
            # create a checkbox for each package
            checkbox = QCheckBox()
            checkbox.setObjectName(package[0])
            checkbox.setText(package[0])
            # set the checkbox to be checked if the package is selected
            # we have "enabled" or "disabled" in the package tuple
            checkbox.setChecked(package[1] == "enabled")
            # Check for a third element in the tuple for version and add as attribute if it exists
            if len(package) > 2:
                checkbox.setProperty("version", package[2])

            row = idx // columns
            col = idx % columns
            options_layout.addWidget(checkbox, row, col)

    def _generate_extras(self, data) -> None:
        extras_layout = self.extras_gb.layout()
        extras = data.get("extras", {})
        columns = 5
        # first remove all existing widgets in the layout
        for i in reversed(range(extras_layout.count())):
            extras_layout.itemAt(i).widget().deleteLater()

        # find any templates to copy
        templates = extras.get("templates", [])
        print(templates)
        print(len(templates))
        for i in range(0, len(templates), 3):
            # create a checkbox for each template
            checkbox = QCheckBox()
            checkbox.setText(templates[i + 2])
            print(templates[i + 2])
            checkbox.setProperty("src", templates[i])
            checkbox.setProperty("dst", templates[i + 1])
            checkbox.setObjectName(f"template_{i + 1}")
            # set the checkbox to be checked if the template is selected
            checkbox.setChecked(True)
            row = i // columns
            col = i % columns
            extras_layout.addWidget(checkbox, row, col)

        toml_data = extras.get("pyproject_extras", [])
        print(data)
        print(toml_data)
        print(extras)
        if toml_data:
            # create a plain text edit for the pyproject.toml extras
            toml_text_edit = QPlainTextEdit()
            for text in toml_data:
                toml_text_edit.appendPlainText(text)
                print(text)
            extras_layout.addWidget(toml_text_edit, len(templates) // columns + 1, 0, 1, columns)

    def load_ui(self) -> None:
        """Load the UI from a .ui file and set up the connections."""
        loader = QUiLoader()
        ui_file = QFile("MainDialog.ui")
        ui_file.open(QFile.ReadOnly)
        # Load the UI into `self` as the parent
        loaded_ui = loader.load(ui_file, self)
        self.setCentralWidget(loaded_ui)
        # add all children with object names to `self`
        for child in loaded_ui.findChildren(QWidget):
            name = child.objectName()
            if name:
                setattr(self, name, child)
        ui_file.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            ...


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
