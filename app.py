"""
app.py

Entry point for launching the StoryKeeper application.
"""

import sys
from PyQt6.QtWidgets import QApplication
from main_window import StoryKeeper


def main() -> None:
    """Initialize and run the StoryKeeper application."""
    app = QApplication(sys.argv)
    window = StoryKeeper()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
