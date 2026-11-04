"""NetDoctor application entry point.

Can be run directly with ``python main.py`` or installed as a console script
via ``netdoctor`` (see ``pyproject.toml``).
"""

import sys

from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("NetDoctor")
    app.setApplicationVersion("2.0.0")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
