"""!@package main

The entrypoint to the main app. It starts the widget and a thread checking for a pendrive with a key.
"""

import sys
import threading

from PySide6 import QtWidgets

from SolutionGUI import SolutionGUI

if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    widget = SolutionGUI()
    widget.resize(800, 600)
    widget.setWindowTitle("Adam Zarzycki 193243")
    widget.show()
    sign_on_start = threading.Thread(widget.sign_if_pendrive_on_start())
    sign_on_start.start()
    sys.exit(app.exec())
