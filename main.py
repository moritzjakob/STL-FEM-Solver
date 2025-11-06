import sys
import os
from PySide6.QtWidgets import QApplication
from fem_app.gui.components.main_window.main_window import MainWindow


def main():
    # Set working directory to project root
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    app = QApplication(sys.argv)
    app.setApplicationName("STL FEM Solver")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
