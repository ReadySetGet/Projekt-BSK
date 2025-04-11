import threading

import win32api
import win32con


class DLThread(threading.Thread):

    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)

    def kill(self):
        win32api.PostThreadMessage(self.ident, win32con.WM_QUIT, 0, 0)
