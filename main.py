from src.main_window.main_window import MainWindow
import sys
from PyQt6.QtWidgets import QApplication
"""main.py"""
if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    app.exec()
     