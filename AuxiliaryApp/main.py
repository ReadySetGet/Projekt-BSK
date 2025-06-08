"""!@package main
The entrypoint to the auxiliary app. It starts the app's widget.
"""

import sys
from PySide6 import QtWidgets

from AuxiliaryGUI import AuxiliaryGUI



if __name__ == '__main__':

    app = QtWidgets.QApplication([])

    widget = AuxiliaryGUI()
    widget.resize(800, 600)
    widget.setWindowTitle("Adam Zarzycki 193243")
    widget.show()

    sys.exit(app.exec())
