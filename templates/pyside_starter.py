#!/usr/bin/env -S uv run --script
import sys

from PySide6.QtCore import QFile, Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QMainWindow,QWidget


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        """Initialize the MainWindow with UI setup and configuration loading."""
        super().__init__()

        self.load_ui()

    def load_ui(self) -> None:
        """Load the UI from a .ui file and set up the connections."""
        try:
            loader = QUiLoader()
            ui_file = QFile("form.ui")
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
            print(f"Error loading UI file: {e}")
            raise

    def keyPressEvent(self, event) -> None:
        """Handle key press events."""
        if event.key() == Qt.Key_Escape:
            self.close()


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)

    try:
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
