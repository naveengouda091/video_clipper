import os
import sys

from core.ffmpeg_locator import get_ffmpeg_path


def launch_gui():
    try:
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QApplication
        from ui.main_window import MainWindow

        # Configure High-DPI attributes if available
        app = QApplication(sys.argv)
        app.setApplicationName("Clipper")
        app.setOrganizationName("Clipper")

        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except ImportError as e:
        print(f"PyQt6 is required for Desktop GUI: {e}")
        print("Please install requirements using: pip install -r requirements.txt")
        sys.exit(1)


def main():
    # If command line arguments were passed (other than script name), run CLI
    if len(sys.argv) > 1:
        from cli import main as cli_main
        cli_main()
    else:
        # Launch modern Desktop GUI
        launch_gui()


if __name__ == "__main__":
    main()
