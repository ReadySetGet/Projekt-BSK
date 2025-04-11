from threading import Thread

from PySide6 import QtCore, QtWidgets
from collections import namedtuple
import time

from PySide6.QtCore import QCoreApplication

from AuxiliaryKeyCreator import AuxiliaryKeyCreator
from DLThread import DLThread
from DeviceListener import DeviceListener


class AuxiliaryGUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        Constants = namedtuple('Constants', ['NR_OF_STAGES'])
        self._constants = Constants(NR_OF_STAGES=6)

        self._current_stage_nr = 0
        self._key_creator = AuxiliaryKeyCreator()

        print("Inicjowanie DeviceListenera...")
        self._listener = DeviceListener(on_change=self.on_devices_changed)

        print("Pobieranie informacji o dyskach...")
        self._is_d_drive_connected = self.find_d_drive()

        print("Inicjowanie GUI...")
        self._d_drive_comm = QtWidgets.QLabel("Pendrive nie jest podpiety" if not self._is_d_drive_connected else "Pendrive jest podpiety")
        self._ending_comm = QtWidgets.QLabel("")
        self._button = QtWidgets.QPushButton("Rozpocznij generowanie")
        self._button_close = QtWidgets.QPushButton("Wyjdź z programu")

        self._layout = QtWidgets.QVBoxLayout(self)

        self._info = QtWidgets.QWidget(self)

        self._grid = QtWidgets.QGridLayout(self._info)

        self._start_texts = ["Podaj PIN:", "Rozpoczęto generacje kluczy", "Rozpoczęto hashowanie PIN-u", "Rozpoczęto szyfrowanie klucza AES-em", "Rozpoczęto zapisywanie klucza publicznego na dysku", "Rozpoczęto zapisywanie klucza prywatnego na pendrivie"]
        self._end_texts = ["Pobrano PIN", "Zakończono generacje kluczy", "Zakończono hashowanie PIN-u", "Zakończono szyfrowanie klucza AES-em", "Zakończono zapisywanie klucza publicznego na dysku", "Zakończono zapisywanie klucza prywatnego na pendrivie"]
        self._ending_comm_text = "Wykonano wszystkie zadania"

        self._stage_comms = []
        self._stage_checks = []
        self._arrows = []

        for i in range(self._constants.NR_OF_STAGES):
            stage_comm = QtWidgets.QLabel("")
            stage_check = QtWidgets.QCheckBox()

            self._stage_comms.append(stage_comm)
            self._stage_checks.append(stage_check)

            arrow = QtWidgets.QLabel("<--")
            arrow.setEnabled(False)

            self._arrows.append(arrow)

            self._grid.addWidget(stage_comm, i, 0, 1, 1, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
            self._grid.addWidget(arrow, i, 1, 1, 1)
            self._grid.addWidget(stage_check, i, 2, 1, 1, alignment=QtCore.Qt.AlignmentFlag.AlignRight)

        self.generation_stages_init()

        self._button.clicked.connect(self.proceed)
        self._button_close.clicked.connect(self.end_listening)
        self._button_close.clicked.connect(QCoreApplication.instance().quit)

        self._grid.setEnabled(False)

        self._button.setEnabled(self._is_d_drive_connected)

        self._layout.addWidget(self._info, alignment=QtCore.Qt.AlignmentFlag.AlignTop)
        self._layout.addWidget(self._d_drive_comm, alignment=QtCore.Qt.AlignmentFlag.AlignBottom)
        self._layout.addWidget(self._ending_comm, alignment=QtCore.Qt.AlignmentFlag.AlignTop)
        self._layout.addWidget(self._button, alignment=QtCore.Qt.AlignmentFlag.AlignBottom)
        self._layout.addWidget(self._button_close, alignment=QtCore.Qt.AlignmentFlag.AlignBottom)

        self._listenerThread = DLThread(target=self._listener.start)
        self._listenerThread.start()
        print("Inicjalizacja zakonczona")

    def generation_stages_init(self):
        for i in range(self._constants.NR_OF_STAGES):
            self._stage_comms[i].setText(self._start_texts[i])

            self._stage_checks[i].setChecked(False)
            self._stage_checks[i].setEnabled(False)

            self._stage_checks[i].hide()
            self._stage_comms[i].hide()
            self._arrows[i].hide()

        self._ending_comm.setText("")
        self._current_stage_nr = 0
    @QtCore.Slot()
    def proceed(self):
        self.generation_stages_init()
        self._grid.setEnabled(True)
        for i in range(self._constants.NR_OF_STAGES):
            self._stage_comms[i].show()
            self._stage_checks[i].show()

        self._button.setEnabled(False)
        self._button.repaint()

        self.show_current_arrow(self._current_stage_nr)
        pin = int(self.ask_for_pin())
        self.set_texts()
        time.sleep(0.5)

        self.show_current_arrow(self._current_stage_nr)
        key_dict = {
            'key_priv': None,
            'key_pub': None
        }
        a = Thread(target=self._key_creator.generate_rsa_keys, args=(key_dict, ))
        a.start()
        while a.is_alive():
            QtWidgets.QApplication.instance().processEvents()
        a.join()
        key_priv = key_dict['key_priv']
        key_pub = key_dict['key_pub']
        self.set_texts()
        time.sleep(0.5)

        self.show_current_arrow(self._current_stage_nr)
        pin_hash = self._key_creator.hash_pin_with_sha256(pin)
        self.set_texts()
        time.sleep(0.5)

        self.show_current_arrow(self._current_stage_nr)
        key_priv_with_aes = self._key_creator.cipher_key_with_aes(pin_hash, key_priv)
        self.set_texts()
        time.sleep(0.5)

        self.show_current_arrow(self._current_stage_nr)
        self._key_creator.write_public_key_to_file(key_pub)
        self.set_texts()
        time.sleep(0.5)

        self.show_current_arrow(self._current_stage_nr)
        b = Thread(target=self._key_creator.write_private_key_to_pendrive, args=(key_priv_with_aes,))
        b.start()
        while b.is_alive():
            QtWidgets.QApplication.instance().processEvents()
        b.join()
        self.set_texts()

        self._arrows[self._current_stage_nr - 1].hide()
        self._ending_comm.setText("Wykonano wszystkie zadania")

        self._button.setEnabled(True)
        self._button.repaint()



    def ask_for_pin(self):
        pin = "a"
        ok = "b"
        while not pin.isdigit():
            pin, ok = QtWidgets.QInputDialog().getText(self, "Wprowadź dane",
                                          "Podaj PIN:", QtWidgets.QLineEdit.EchoMode.Normal,
                                          QtCore.QDir().home().dirName())

        if ok and pin:
            self._stage_comms[self._current_stage_nr].setText(self._end_texts[self._current_stage_nr])
            self._stage_checks[self._current_stage_nr].setChecked(True)
            return pin

    def show_current_arrow(self, idx):
        if idx != 0:
            self._arrows[idx-1].hide()
        self._arrows[idx].show()
        self._arrows[idx].repaint()


    def set_texts(self):
        self._stage_comms[self._current_stage_nr].setText(self._end_texts[self._current_stage_nr])
        self._stage_checks[self._current_stage_nr].setChecked(True)
        self._current_stage_nr += 1

    def find_d_drive(self):
        drives = self._listener.list_drives()
        removable_drives = [d for d in drives if d.is_removable]
        for drive in removable_drives:
            if drive.letter == 'D:':
                return True

        return False

    def on_devices_changed(self):
        self._d_drive_comm.setText("Sprawdzam zmiany urzadzen zewnetrznych...")
        self._d_drive_comm.repaint()
        self._button.setEnabled(False)
        self._button.repaint()
        is_found = self.find_d_drive()
        if not self._is_d_drive_connected and is_found:
            self._is_d_drive_connected = True
            self._d_drive_comm.setText("Pendrive jest podpiety")
            self._button.setEnabled(True)
        elif self._is_d_drive_connected and not is_found:
            self._is_d_drive_connected = False
            self._d_drive_comm.setText("Pendrive nie jest podpiety")
            self._button.setEnabled(False)

        self._d_drive_comm.repaint()
        self._button.repaint()
        self.repaint()

    def end_listening(self):
        self._listenerThread.kill()
        self._listenerThread.join()
