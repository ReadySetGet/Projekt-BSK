"""!@package SolutionGUI
It revolves around the user interface of the main application, controls the processes of
signing/verification, and enables them based on feedback from [DeviceListener](#DeviceListener).
"""

from PySide6 import QtCore, QtWidgets
from collections import namedtuple
import time

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QFileDialog

from DLThread import DLThread
from DeviceListener import DeviceListener
from SolutionHashComparer import SolutionHashComparer
from SolutionPDFSigner import SolutionPDFSigner
from pathlib import Path

import os


class SolutionGUI(QtWidgets.QWidget):
    """!The main app GUI class. It realizes all the functionalities of this package."""


    def __init__(self):
        """!Constructor. It Initializes all the widget's elements, used constants, and places them in the layout."""
        super().__init__()

        Constants = namedtuple('Constants', ['NR_OF_STAGES_SIGNING', 'NR_OF_STAGES_VERIFYING'])
        self._constants = Constants(NR_OF_STAGES_SIGNING=6, NR_OF_STAGES_VERIFYING=3)

        self._current_stage_nr = 0
        self._signer: SolutionPDFSigner = None
        self._hash_comparer = SolutionHashComparer()

        print("Inicjowanie DeviceListenera...")
        self._listener = DeviceListener(on_change=self.on_devices_changed)

        print("Pobieranie informacji o dyskach...")
        self._is_d_drive_connected = self.find_d_drive()

        print("Inicjowanie GUI...")
        self._d_drive_comm = QtWidgets.QLabel("Pendrive nie jest podpięty" if not self._is_d_drive_connected else "Pendrive jest podpięty, klucz został pobrany")
        self._ending_comm = QtWidgets.QLabel("")
        self._result_comm = QtWidgets.QLabel("")
        self._button_sign = QtWidgets.QPushButton("Rozpocznij podpisywanie")
        self._button_verify = QtWidgets.QPushButton("Rozpocznij weryfikacje")
        self._button_close = QtWidgets.QPushButton("Wyjdź z programu")

        self._layout = QtWidgets.QVBoxLayout(self)

        self._info = QtWidgets.QWidget(self)

        self._grid = QtWidgets.QGridLayout(self._info)

        self._start_texts_sign = ["Podaj PIN:", "Wybieranie dokumentu", "Rozpoczęto hashowanie PIN-u", "Rozpoczęto deszyfrowanie klucza", "Rozpoczęto przygotowanie dokumentu", "Rozpoczęto podpisywanie dokumentu"]
        self._end_texts_sign = ["Pobrano PIN", "Zakończono wybieranie dokumentu", "Zakończono hashowanie PIN-u", "Zakończono deszyfrowanie klucza", "Zakończono przygotowanie dokumentu", "Zakończono podpisywanie dokumentu"]

        self._start_texts_verify = ["Wybieranie dokumentu", "Rozpoczęto pobieranie klucza publicznego",
                                  "Rozpoczęto weryfikację"]
        self._end_texts_verify = ["Zakończono wybieranie dokumentu", "Zakończono pobieranie klucza publicznego",
                                "Zakończono weryfikację"]

        self._ending_comm_text = "Wykonano wszystkie zadania"

        self._stage_comms = []
        self._stage_checks = []
        self._arrows = []

        for i in range(self._constants.NR_OF_STAGES_SIGNING):
            stage_comm = QtWidgets.QLabel("")
            stage_check = QtWidgets.QCheckBox()

            self._stage_comms.append(stage_comm)
            self._stage_checks.append(stage_check)

            arrow = QtWidgets.QLabel("<--")
            arrow.setEnabled(True)

            self._arrows.append(arrow)

            self._grid.addWidget(stage_comm, i, 0, 1, 1, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
            self._grid.addWidget(arrow, i, 1, 1, 1)
            self._grid.addWidget(stage_check, i, 2, 1, 1, alignment=QtCore.Qt.AlignmentFlag.AlignRight)

        self.generation_stages_init()

        self._button_sign.clicked.connect(self.proceed_sign)
        self._button_verify.clicked.connect(self.proceed_verify)
        self._button_close.clicked.connect(self.end_listening)
        self._button_close.clicked.connect(QCoreApplication.instance().quit)

        self._grid.setEnabled(False)

        self._button_sign.setEnabled(self._is_d_drive_connected)
        self._button_verify.setEnabled(True)

        self._layout.addWidget(self._info, alignment=QtCore.Qt.AlignmentFlag.AlignTop)
        self._layout.addWidget(self._d_drive_comm, alignment=QtCore.Qt.AlignmentFlag.AlignBottom)
        self._layout.addWidget(self._ending_comm, alignment=QtCore.Qt.AlignmentFlag.AlignTop)
        self._layout.addWidget(self._result_comm, alignment=QtCore.Qt.AlignmentFlag.AlignTop)
        self._layout.addWidget(self._button_sign, alignment=QtCore.Qt.AlignmentFlag.AlignBottom)
        self._layout.addWidget(self._button_verify, alignment=QtCore.Qt.AlignmentFlag.AlignBottom)
        self._layout.addWidget(self._button_close, alignment=QtCore.Qt.AlignmentFlag.AlignBottom)

        self._listenerThread = DLThread(target=self._listener.start)
        self._listenerThread.start()
        print("Inicjalizacja zakończona")

    def generation_stages_init(self):
        """!\brief It brings back the *default settings* of the app.

        It brings back the *default settings* of the app, clearing all the labels and enabling the buttons accordingly
        (based on whether the pendrive is available).
        """

        for i in range(self._constants.NR_OF_STAGES_SIGNING):
            self._stage_comms[i].setText("")

            self._stage_checks[i].setChecked(False)
            self._stage_checks[i].setEnabled(False)

            self._stage_checks[i].hide()
            self._stage_comms[i].hide()
            self._arrows[i].hide()

        self._ending_comm.setText("")
        self._result_comm.setText("")
        self._current_stage_nr = 0

    @QtCore.Slot()
    def proceed_sign(self):
        """!\brief Controller of the signing process.

        Controller of the signing process. It resets the app with `generation_stages_init()`, and executes all the steps
         necessary for the signing process to succeed, by invoking the adequate methods of
         [SolutionPDFSigner](#SolutionPDFSigner) class. It shows the user all relevant progress messages, and changes
         the position of the progress arrow. Lastly, it presents the result of actions taken to the user.
        """

        self.generation_stages_init()
        self._grid.setEnabled(True)
        for i in range(self._constants.NR_OF_STAGES_SIGNING):
            self._stage_comms[i].show()
            self._stage_checks[i].show()
            self._stage_comms[i].setText(self._start_texts_sign[i])

        self._button_sign.setEnabled(False)
        self._button_sign.repaint()

        self._button_verify.setEnabled(False)
        self._button_verify.repaint()

        self.show_current_arrow(self._current_stage_nr)
        pin = int(self.ask_for_pin())
        self.set_texts_sign()
        time.sleep(0.5)

        self.show_current_arrow(self._current_stage_nr)
        fileName = QFileDialog.getOpenFileName(self, "Open PDF", "C:\Studia\BSK\ProjektBSK\pdfs", "PDF Files (*.pdf)")[0]
        name, path = os.path.basename(fileName), os.path.dirname(fileName) + '/'
        if name == "":
            self.generation_stages_init()
            self._button_sign.setEnabled(True if self._is_d_drive_connected else False)
            self._button_sign.repaint()

            self._button_verify.setEnabled(True)
            self._button_verify.repaint()
            self._result_comm.setText("Brak wybranego pliku")
            return
        self._signer.set_file(path, name)
        self.set_texts_sign()
        time.sleep(0.5)

        self.show_current_arrow(self._current_stage_nr)
        self._signer.hash_pin(pin)
        self.set_texts_sign()
        time.sleep(0.5)

        self.show_current_arrow(self._current_stage_nr)
        was_good_pin = self._signer.decrypt()
        if not was_good_pin:
            self.generation_stages_init()
            self._button_sign.setEnabled(True if self._is_d_drive_connected else False)
            self._button_sign.repaint()

            self._button_verify.setEnabled(True)
            self._button_verify.repaint()
            self._result_comm.setText("Niepoprawny klucz")
            return
        self.set_texts_sign()
        time.sleep(0.5)

        self.show_current_arrow(self._current_stage_nr)
        was_signed = self._signer.prepare_file()
        if was_signed == 0:
            self.generation_stages_init()
            self._button_sign.setEnabled(True if self._is_d_drive_connected else False)
            self._button_sign.repaint()

            self._button_verify.setEnabled(True)
            self._button_verify.repaint()
            self._result_comm.setText("Plik jest już podpisany")
            return
        elif was_signed == -1:
            self.generation_stages_init()
            self._button_sign.setEnabled(True if self._is_d_drive_connected else False)
            self._button_sign.repaint()

            self._button_verify.setEnabled(True)
            self._button_verify.repaint()
            self._result_comm.setText("Nie mam uprawnień do edycji pliku")
            return
        self.set_texts_sign()
        time.sleep(0.5)

        self.show_current_arrow(self._current_stage_nr)
        self._signer.sign()
        self.set_texts_sign()
        time.sleep(0.5)

        self._arrows[self._current_stage_nr - 1].hide()
        self._ending_comm.setText("Wykonano wszystkie zadania")
        self._result_comm.setText("Poprawnie podpisano dokument")

        self._button_sign.setEnabled(True)
        self._button_sign.repaint()

        self._button_verify.setEnabled(True)
        self._button_verify.repaint()

    @QtCore.Slot()
    def proceed_verify(self):
        """!\brief Controller of the verifying process.

        Controller of the verifying process. It resets the app with `generation_stages_init()`, and executes all
         the steps necessary for the signing process to succeed, by invoking the adequate methods of
        [SolutionHashComparer](#SolutionHashComparer) class. It shows the user all relevant progress messages,
         and changes the position of the progress arrow. Lastly, it presents the result of actions taken to the
        user.
        """

        self.generation_stages_init()
        self._grid.setEnabled(True)
        for i in range(self._constants.NR_OF_STAGES_VERIFYING):
            self._stage_comms[i].show()
            self._stage_checks[i].show()
            self._stage_comms[i].setText(self._start_texts_verify[i])

        self._button_sign.setEnabled(False)
        self._button_sign.repaint()

        self._button_verify.setEnabled(False)
        self._button_verify.repaint()

        self.show_current_arrow(self._current_stage_nr)
        fileName = QFileDialog.getOpenFileName(self, "Open PDF", "C:\Studia\BSK\ProjektBSK\pdfs", "PDF Files (*.pdf)")[0]
        name, path = os.path.basename(fileName), os.path.dirname(fileName)+'/'
        if name == "":
            self.generation_stages_init()
            self._button_sign.setEnabled(True if self._is_d_drive_connected else False)
            self._button_sign.repaint()

            self._button_verify.setEnabled(True)
            self._button_verify.repaint()
            self._result_comm.setText("Brak wybranego pliku")
            return
        self._hash_comparer.set_file(path, name)
        self.set_texts_verify()
        time.sleep(0.5)

        self.show_current_arrow(self._current_stage_nr)
        self._hash_comparer.set_public_key()
        self.set_texts_verify()
        time.sleep(0.5)

        self.show_current_arrow(self._current_stage_nr)
        valid = self._hash_comparer.verify()
        if valid == -1:
            self.generation_stages_init()
            self._button_sign.setEnabled(True if self._is_d_drive_connected else False)
            self._button_sign.repaint()

            self._button_verify.setEnabled(True)
            self._button_verify.repaint()
            self._result_comm.setText("Plik nie jest podpisany")
            return
        self.set_texts_verify()
        time.sleep(0.5)

        self._arrows[self._current_stage_nr - 1].hide()
        self._ending_comm.setText("Wykonano wszystkie zadania")
        self._result_comm.setText("Weryfikacja się udała - dokument jest poprawny" if valid == 1 else "Weryfikacja się nie powiodła - dokument był zmieniany")

        self._button_sign.setEnabled(True if self._is_d_drive_connected else False)
        self._button_sign.repaint()

        self._button_verify.setEnabled(True)
        self._button_verify.repaint()

    def ask_for_pin(self):
        """!\brief Getting pin from the user

        It shows a `QInputDialog` instance to the user, and checks whether the pin provided has numerical value.
        """

        pin = "a"
        ok = "b"
        while not pin.isdigit():
            pin, ok = QtWidgets.QInputDialog().getText(self, "Wprowadź dane",
                                          "Podaj PIN:", QtWidgets.QLineEdit.EchoMode.Normal,
                                          QtCore.QDir().home().dirName())

        if ok and pin:
            self._stage_comms[self._current_stage_nr].setText(self._end_texts_sign[self._current_stage_nr])
            self._stage_checks[self._current_stage_nr].setChecked(True)
            return pin

    def show_current_arrow(self, idx):
        """!Changes position of the arrow showing currently executed stage to the next stage."""

        if idx != 0:
            self._arrows[idx-1].hide()
        self._arrows[idx].show()
        self._arrows[idx].repaint()


    def set_texts_sign(self):
        """!A `proceed_sign()` helper function, changing the messages of the executed stages to their "done"
        counterparts, and marking them as such.
        """

        self._stage_comms[self._current_stage_nr].setText(self._end_texts_sign[self._current_stage_nr])
        self._stage_checks[self._current_stage_nr].setChecked(True)
        self._current_stage_nr += 1

    def set_texts_verify(self):
        """!A `proceed_verify()` helper function, changing the messages of the executed stages to their "done"
        counterparts, and marking them as such.
        """

        self._stage_comms[self._current_stage_nr].setText(self._end_texts_verify[self._current_stage_nr])
        self._stage_checks[self._current_stage_nr].setChecked(True)
        self._current_stage_nr += 1

    def find_d_drive(self):
        """!\brief Checking the pendrive's status.

        It calls the listener's `list_drives()` function, and checks if the pendrive (with a private key present) is
        amongst them.

        \return (bool) whether the pendrive with a key was found or
        """

        drives = self._listener.list_drives()
        removable_drives = [d for d in drives if d.is_removable]
        for drive in removable_drives:
            if drive.letter == 'D:':
                my_file = Path("D:/ProjectBSKPrivateKey.pem")
                if my_file.is_file():
                    return True

        return False

    def on_devices_changed(self):
        """!\brief Checking the device setup changes.

        It's called by [DeviceListener](#DeviceListener) class when a change in drives' configuration has been detected.
         It calls the `find_d_drive()` method to ascertain the desired pendrive's presence, and if so, it loads the
         encrypted private key (via initializing the [SolutionPDFSigner](#SolutionPDFSigner) class), and starts the
         signing process.
        """

        self._d_drive_comm.setText("Sprawdzam zmiany urzadzeń zewnętrznych...")
        self._d_drive_comm.repaint()
        self._button_sign.setEnabled(False)
        self._button_sign.repaint()
        self._button_verify.setEnabled(False)
        self._button_verify.repaint()
        is_found = self.find_d_drive()
        flag = False
        if not self._is_d_drive_connected and is_found:
            self._is_d_drive_connected = True
            self._d_drive_comm.setText("Pendrive z kluczem jest podpięty, klucz został pobrany")
            self._button_sign.setEnabled(True)
            flag = True
        elif self._is_d_drive_connected and not is_found:
            self._is_d_drive_connected = False
            self._d_drive_comm.setText("Pendrive nie jest podpięty lub brak klucza")
            self._button_sign.setEnabled(False)

        self._button_verify.setEnabled(True)

        self._d_drive_comm.repaint()
        self._button_sign.repaint()
        self._button_verify.repaint()
        self.repaint()

        if flag:
            self._signer = SolutionPDFSigner()
            self._button_sign.click()

    def end_listening(self):
        """!A method for ending the listener's thread."""

        self._listenerThread.kill()
        self._listenerThread.join()

    def sign_if_pendrive_on_start(self):
        """!A method for a thread to check whether the app should load the key and start the signing proccess on
        execution.
        """

        if self._is_d_drive_connected:
            self._signer = SolutionPDFSigner()
            self._button_sign.click()