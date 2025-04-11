import json
import logging
import subprocess
from dataclasses import dataclass
from typing import Callable, List

import win32api, win32con, win32gui


@dataclass
class Drive:
    letter: str
    label: str
    drive_type: str

    @property
    def is_removable(self) -> bool:
        return self.drive_type == 'Removable Disk'


class DeviceListener:

    WM_DEVICECHANGE_EVENTS = {
        0x0019: ('DBT_CONFIGCHANGECANCELED', 'A request to change the current configuration (dock or undock) has been canceled.'),
        0x0018: ('DBT_CONFIGCHANGED', 'The current configuration has changed, due to a dock or undock.'),
        0x8006: ('DBT_CUSTOMEVENT', 'A custom event has occurred.'),
        0x8000: ('DBT_DEVICEARRIVAL', 'A device or piece of media has been inserted and is now available.'),
        0x8001: ('DBT_DEVICEQUERYREMOVE', 'Permission is requested to remove a device or piece of media. Any application can deny this request and cancel the removal.'),
        0x8002: ('DBT_DEVICEQUERYREMOVEFAILED', 'A request to remove a device or piece of media has been canceled.'),
        0x8004: ('DBT_DEVICEREMOVECOMPLETE', 'A device or piece of media has been removed.'),
        0x8003: ('DBT_DEVICEREMOVEPENDING', 'A device or piece of media is about to be removed. Cannot be denied.'),
        0x8005: ('DBT_DEVICETYPESPECIFIC', 'A device-specific event has occurred.'),
        0x0007: ('DBT_DEVNODES_CHANGED', 'A device has been added to or removed from the system.'),
        0x0017: ('DBT_QUERYCHANGECONFIG', 'Permission is requested to change the current configuration (dock or undock).'),
        0xFFFF: ('DBT_USERDEFINED', 'The meaning of this message is user-defined.'),
    }

    def __init__(self, on_change: Callable[[], None]):
        self.on_change = on_change

    def _create_window(self):
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self._on_message
        wc.lpszClassName = self.__class__.__name__
        wc.hInstance = win32api.GetModuleHandle(None)
        class_atom = win32gui.RegisterClass(wc)
        return win32gui.CreateWindow(class_atom, self.__class__.__name__, 0, 0, 0, 0, 0, 0, 0, wc.hInstance, None)

    def start(self):
        self.hwnd = self._create_window()
        win32gui.PumpMessages()

    def close(self):
        win32gui.CloseWindow(self.hwnd)

    def _on_message(self, hwnd: int, msg: int, wparam: int, lparam: int):
        if msg != win32con.WM_DEVICECHANGE:
            return 0
        event, description = self.WM_DEVICECHANGE_EVENTS[wparam]
        if event in ('DBT_DEVICEREMOVECOMPLETE', 'DBT_DEVICEARRIVAL'):
            self.on_change()
        return 0

    @staticmethod
    def list_drives() -> List[Drive]:
        proc = subprocess.run(
            args=[
                'powershell',
                '-noprofile',
                '-command',
                'Get-WmiObject -Class Win32_LogicalDisk | Select-Object deviceid,volumename,drivetype | ConvertTo-Json'
            ],
            text=True,
            stdout=subprocess.PIPE
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return []
        devices = json.loads(proc.stdout)

        drive_types = {
            0: 'Unknown',
            1: 'No Root Directory',
            2: 'Removable Disk',
            3: 'Local Disk',
            4: 'Network Drive',
            5: 'Compact Disc',
            6: 'RAM Disk',
        }

        return [Drive(
            letter=d['deviceid'],
            label=d['volumename'],
            drive_type=drive_types[d['drivetype']]
        ) for d in devices]

