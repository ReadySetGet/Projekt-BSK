"""!@package DLThread
A wrapper for python's `threading.Thread` class, with added [DeviceListener](#DeviceListener) stopping capabilities.
"""

import threading

import win32api
import win32con


class DLThread(threading.Thread):
    """!The main class, inheriting from `threading.Thread` python class."""

    def __init__(self, *args, **keywords):
        """!Constructor."""

        super().__init__(*args, **keywords)

    def kill(self):
        """!It stops the associated listener by sending an appropriate win32api message."""

        win32api.PostThreadMessage(self.ident, win32con.WM_QUIT, 0, 0)
