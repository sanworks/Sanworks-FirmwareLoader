#!/usr/bin/env python3

import os
import subprocess
import sys

from PyQt6 import QtGui
from PyQt6.QtCore import QSettings, QPoint, QSize, QTimer, Qt
from PyQt6.QtWidgets import QApplication, QLabel, QComboBox, QPushButton, QMessageBox, QDialog, QPlainTextEdit
from serial.tools.list_ports import comports

VERSION = "0.9.9"


class FirmwareUpdater:
    """ Wraps a directory containing firmware files (`firmware_path`) with a simple API """

    def __init__(self, firmware_path=None):
        # Get bossac and tycmd paths and versions
        self.bossac_path = self._get_bossac_path()
        self.tycmd_path = self._get_tycmd_path()
        self.bossac_version = self._get_bossac_version()
        self.tycmd_version = self._get_tycmd_version()

        # Parse the firmware_path
        self.firmware_path = firmware_path or os.path.join(os.getcwd(), 'firmware')
        self.firmware = {}
        for fname in os.listdir(self.firmware_path):
            name = " ".join(fname.split('_')[:-1])
            extension = fname.split('.')[-1].lower()
            if extension in ('bin', 'hex'):
                version = fname.split('_')[-1][:len(extension) + 1][1:]
                loader = extension == 'bin' and 'bossac' or extension == 'hex' and 'tycmd' or None
                fpath = os.path.join(self.firmware_path, fname)
                self.firmware[name] = self.firmware.get(name, []) + [{
                    'fname': fname,
                    'fpath': fpath,
                    'extension': extension,
                    'version': version,
                    'loader': loader,
                }]

        # Sort each named group descending by version
        for fwname in self.firmware:
            self.firmware[fwname].sort(key=lambda d: d['version'], reverse=True)

    def _which(self, program) -> str:
        """ get the full path to an executable `program` on the path; or an empty string """
        if 'win' in sys.platform:
            for path in os.environ.get("PATH", "").split(os.pathsep):
                exe_file = os.path.join(path, program)
                if os.path.isfile(exe_file) and os.access(exe_file, os.X_OK):
                    return exe_file
            return ""
        else:
            try:
                return subprocess.check_output(f"which {program}", shell=True).decode().strip()
            except subprocess.CalledProcessError:
                return ""

    def _get_bossac_path(self):
        """ default to our bossac on Windows; otherwise try to use one on the path """
        _path = self._which('bossac')
        if 'win' in sys.platform:
            _path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'third_party\\bossac\\bossac.exe')
        return os.path.exists(_path) and _path or ""

    def _get_tycmd_path(self):
        """ default to our tycmd on Windows; otherwise try to use one on the path before using ours """
        _path = self._which('tycmd')
        if 'win' in sys.platform:
            _path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'third_party\\tycmd\\tycmd.exe')
        if not _path:
            if 'linux' in sys.platform:
                _path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'third_party/tycmd/tycmd_linux64')
            elif 'darwin' in sys.platform:
                _path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'third_party/tycmd/tycmd_osx')
        return os.path.exists(_path) and _path or ""

    def _get_bossac_version(self) -> str:
        """ return the version of bossac represented at self.bossac_path """
        _version = ""
        if self.bossac_path:
            try:
                _version = next(iter([
                    line.split(' Version ')[-1] for line in subprocess.run(
                        [self.bossac_path, '--help'],
                        stdout=subprocess.PIPE,
                        universal_newlines=True
                    ).stdout.splitlines() if ' Version ' in line
                ]), "").strip()
            except subprocess.CalledProcessError:
                return _version
        return _version

    def _get_tycmd_version(self) -> str:
        """ return the version of tycmd represented at self.tycmd_path """
        _version = ""
        if self.tycmd_path:
            try:
                _version = subprocess.check_output(
                    f"{self.tycmd_path} --version", shell=True
                ).decode().strip().split()[-1]
            except subprocess.CalledProcessError:
                return _version
        return _version

    def get_firmware_names(self) -> list:
        """ return a list of available firmware names """
        return list(self.firmware.keys())

    def get_firmware_versions(self, name: str) -> list:
        """ return a list of available versions for a given firmware name """
        return [fd['version'] for fd in self.firmware.get(name, [])]

    def get_firmware(self, name: str, version: str) -> dict:
        """ return the firmware dict for the matching `name` and `version` """
        return next(iter([fd for fd in self.firmware.get(name, []) if fd['version'] == version]), {})

    def get_firmware_update_commands(self, firmware: dict, serial_port: str) -> list:
        """ return a list of string commands necessary to load `firmware` onto `serial_port` """
        _commands = []
        if firmware['loader'] == 'bossac':
            if 'win' in sys.platform:
                _commands.append(f"mode {serial_port}:1200,N,8,1")
                _commands.append("PING -n 3 127.0.0.1>NUL")
                _commands.append(f"{self.bossac_path} -i -U true -e -w -v -b {firmware['fpath']} -R")
            else:
                _commands.append(f"{self.bossac_path} -i -d -U=true -e -w -v -b {firmware['fpath']} -R")
        elif firmware['loader'] == 'tycmd':
            if serial_port.isdigit():
                _commands.append(f"{self.tycmd_path} upload {firmware['fpath']} --board {serial_port}")
            else:
                _commands.append(f"{self.tycmd_path} upload {firmware['fpath']} --board @{serial_port}")
        return _commands

    def get_serial_port_strings(self) -> list:
        """ return a list of serial port strings suitable for display and reparsing """
        _ports = []

        # First, use pyserial to get "normal" serial ports...
        for port in comports():
            if port.vid and port.pid:   # Only include USB Serial Devices; do not include hardware / "actual" serial ports
                hexvid = format(port.vid, 'X').zfill(4)
                hexpid = format(port.pid, 'X').zfill(4)
                if hexvid not in ('0403', '067B'):  # Do not include USB-to-Serial converters (FTDI/Prolific)
                    if hexvid in ("2341",):     # Arduino
                        if port.serial_number:
                            _ports.append(f"{port.device} -> Arduino (SN# {port.serial_number.replace('&', '')})")
                        else:
                            _ports.append(f"{port.device} -> Arduino")
                    elif hexvid in ("16C0",):   # Teensy
                        if port.serial_number:
                            _ports.append(f"{port.device} -> Teensy (SN# {port.serial_number})")
                        else:
                            _ports.append(f"{port.device} -> Teensy")
                    else:   # Unknown (not Arduino or Teensy)
                        if port.serial_number:
                            _ports.append(f"{port.device} -> {hexvid}:{hexpid} (SN# {port.serial_number})")
                        else:
                            _ports.append(f"{port.device} -> {hexvid}:{hexpid}")

        # Then, use tycmd to get Teensyduino RawHID devices (Teensies that haven't yet been programmed)...
        if self.tycmd_path:
            for line in subprocess.run([self.tycmd_path, "list"], stdout=subprocess.PIPE, universal_newlines=True).stdout.splitlines():
                if line.startswith("add ") and "(Teensyduino RawHID)" in line:
                    _ports.append(f"{line[4:12]} -> {line[20:]}")

        # Finally, sort numerically and return!
        _ports.sort(key=lambda p: int("0" + "".join([x for x in p.split('->')[0].strip() if x.isdigit()])))
        return _ports

    def get_serial_port_device_name(self, port_string) -> str:
        """ Returns the device name from a display string """
        return port_string.split('->')[0].strip()


FIRMWARE_UPDATER_STYLE = """
#MainWindow,
#FirmwareLoaderMessageBox{
    color: #1aff1a; background: #000000 url(assets/FirmwareBG.bmp);
}
QLabel{
    color: #1aff1a;
}
QPushButton{
    color: #1aff1a; background: #000000;
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #111111, stop: 1 #113311);
    text-transform:uppercase; font-family: monospace;
}
#LoadButton{
    font-size: 18pt; font-weight:bold;
    border: 2px dotted #00FF00;
    padding: 15px 15px;
}
#RescanButton{
    font-size: 11pt;
    border: 2px dotted #00FF00;
    padding: 2px 6px;
}
QComboBox,
QAbstractItemView {
    color: #1aff1a; background: #000000;
    font-size: 12pt; font-weight: bold;
    border: 1px solid #00FF00;
}
#LogWindow{
    color:#1aff1a; background:#000000;
}
"""



class FirmwareUpdaterMainWindow(QDialog):
    """ PyQt6 GUI for Updating Firmware, using the FirmwareUpdater API """

    S_WindowTitle = "Sanworks Firmware Loading Tool"
    S_WindowTitle_WAIT = "Sanworks Firmware Loading Tool        [ PLEASE WAIT ]"

    def __init__(self, *args, firmware_path=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = QSettings('Sanworks', 'FirmwareUpdater')
        self.move(self.settings.value("pos", QPoint(100, 100)))
        self.resize(QSize(560, 420))
        self.setWindowTitle(self.S_WindowTitle)
        self.setWindowIcon(QtGui.QIcon('assets/SanworksIcon.bmp'))
        self.setStyleSheet(FIRMWARE_UPDATER_STYLE)
        self.setObjectName("MainWindow")

        self.firmware_path = firmware_path or os.path.join(os.getcwd(), 'firmware')
        self.firmware_updater = FirmwareUpdater(firmware_path=self.firmware_path)

        firmware_label = QLabel("<h1>Firmware</h1>", parent=self)
        firmware_label.move(20, 20)
        self.firmware_combo = QComboBox(parent=self)
        self.firmware_combo.addItems(self.firmware_updater.get_firmware_names())
        self.firmware_combo.setMinimumWidth(400)
        self.firmware_combo.move(20, 60)
        self.firmware_combo.setCurrentIndex(
            self.firmware_combo.findText(
                self.settings.value("firmwareName", self.firmware_combo.currentText())
            )
        )
        self.firmware_combo.currentTextChanged.connect(self._firmware_combo_changed)

        version_label = QLabel("<h2>Version</h2>", parent=self)
        version_label.move(440, 20)
        self.version_combo = QComboBox(parent=self)
        self.version_combo.addItems(self.firmware_updater.get_firmware_versions(self.firmware_combo.currentText()))
        self.version_combo.setMinimumWidth(100)
        self.version_combo.move(440, 60)

        device_label = QLabel("<h1>Device</h1>", parent=self)
        device_label.move(20, 110)
        self.device_combo = QComboBox(parent=self)
        self.device_combo.addItems(self.firmware_updater.get_serial_port_strings())
        self.device_combo.setMinimumWidth(400)
        self.device_combo.move(20, 150)

        self.rescan_button = QPushButton("Rescan", parent=self)
        self.rescan_button.setObjectName("RescanButton")
        self.rescan_button.setMinimumWidth(100)
        self.rescan_button.move(320, 115)
        self.rescan_button.clicked.connect(self._rescan_button_clicked)

        self.load_button = QPushButton("Load", parent=self)
        self.load_button.setObjectName("LoadButton")
        self.load_button.move(440, 115)
        self.load_button.clicked.connect(self._load_button_clicked)

        self.log_window = QPlainTextEdit(parent=self)
        self.log_window.setObjectName("LogWindow")
        self.log_window.move(20, 200)
        self.log_window.resize(QSize(520, 200))
        self.log_window.setReadOnly(True)

        self.msgBox = QMessageBox(parent=self)
        self.msgBox.setObjectName("FirmwareLoaderMessageBox")
        self.msgBox.setWindowTitle("Firmware Update Status")
        self.msgBox.setStandardButtons(QMessageBox.StandardButton.Ok)

        self.print_version_text()
        self.refresh_device_combo()
        self.print_sanitycheck()

    def print_version_text(self):
        """ Prints the Firmware Updater Version to the log_window """
        self.log_window.appendPlainText(f"Sanworks Firmware Updater v{VERSION}")

    def print_sanitycheck(self):
        # Each individual check...
        # Bossac
        if self.firmware_updater.bossac_path and self.firmware_updater.bossac_version:
            self.log_window.appendPlainText(f"Using bossac version {self.firmware_updater.bossac_version} from")
            self.log_window.appendPlainText(f"    {os.path.dirname(self.firmware_updater.bossac_path)}")
        else:
            self.log_window.appendPlainText("WARNING: BOSSAC NOT FOUND.")
        # Tycmd
        if self.firmware_updater.tycmd_path and self.firmware_updater.tycmd_version:
            self.log_window.appendPlainText(f"Using tycmd version {self.firmware_updater.tycmd_version} from")
            self.log_window.appendPlainText(f"    {os.path.dirname(self.firmware_updater.tycmd_path)}")
        else:
            self.log_window.appendPlainText("WARNING: TYCMD NOT FOUND.")
        # Serial devices
        if len(self.device_combo):
            self.log_window.appendPlainText(
                f"Detected {len(self.device_combo)} serial device{len(self.device_combo) == 1 and '' or 's'}"
            )
        if not len(self.device_combo):
            self.log_window.appendPlainText("WARNING: NO SERIAL DEVICES DETECTED.")

        # Summary message...
        if all((self.firmware_updater.bossac_path, self.firmware_updater.tycmd_path, len(self.device_combo),)):
            self.log_window.appendPlainText("\nREADY TO LOAD!")
        else:
            self.log_window.appendPlainText("\nNOT READY TO LOAD!")

    def _firmware_combo_changed(self, text):
        self.version_combo.clear()
        self.version_combo.addItems(self.firmware_updater.get_firmware_versions(text))

    def _load_button_clicked(self, e):
        """ Load the Firmware """
        if self.firmware_combo.currentText() and self.device_combo.currentText():
            # Rehydrate everything and start logging to the log_window...
            firmware = self.firmware_updater.get_firmware(self.firmware_combo.currentText(), self.version_combo.currentText())
            serial_port = self.firmware_updater.get_serial_port_device_name(self.device_combo.currentText())
            self.log_window.clear()
            self.print_version_text()
            self.log_window.appendPlainText(f"Loading {firmware['fpath']} to {serial_port} with {firmware['loader']}...")
            self.setWindowTitle(self.S_WindowTitle_WAIT)
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

            # Actually run the commands...
            self._commands = self.firmware_updater.get_firmware_update_commands(firmware, serial_port)
            self._current_command_index = 0
            self._command_states = []
            self._execute_commands()

        else:  # We can't load the firmware!
            self.log_window.clear()
            self.print_version_text()
            self.log_window.appendPlainText("Please select a firmware image and serial device.")
            self.msgBox.setIcon(QMessageBox.Icon.Critical)
            self.msgBox.setText("<h1>EPIC FAIL</h1><h2>You must select a firmware image<br>and serial device!</h2>")
            self.msgBox.exec()

    def _execute_commands(self):
        if self._current_command_index < len(self._commands):
            self._command_states.append(
                self._execute_command(
                    self._commands[self._current_command_index]
                )
            )
        else:
            QApplication.restoreOverrideCursor()
            self.setWindowTitle(self.S_WindowTitle)
            if all(self._command_states):
                self.log_window.appendPlainText("GREAT SUCCESS!")
                self.msgBox.setIcon(QMessageBox.Icon.Information)
                self.msgBox.setText("<h1>GREAT SUCCESS!</h1><h2>Firmware loading has succeeded.<br></h2>")
            else:
                self.log_window.appendPlainText("EPIC FAIL: Some commands FAILED to run.")
                self.msgBox.setIcon(QMessageBox.Icon.Critical)
                self.msgBox.setText(
                    "<h1>EPIC FAIL</h1><h2>Firmware loading failed.<br>Please review the log window for details.</h2>"
                )
            self.msgBox.exec()

    def _execute_command(self, command) -> bool:
        # Munge the command so it runs in the shell. This makes it so that builtins work.
        if 'win' in sys.platform:
            shell_command = ["cmd", "/c", command]
        else:
            shell_command = ["sh", "-c", command]

        # Actually execute the command; pipe all output to the log_window
        process = subprocess.Popen(
            shell_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        output = stdout.strip() if stdout else stderr.strip()
        self.log_window.appendPlainText(output)

        # Schedule execution of next command after a short delay
        QTimer.singleShot(1000, self._next_command)

        # Return True if the command exited cleanly, False otherwise
        return not bool(process.returncode)

    def _next_command(self):
        self._current_command_index += 1
        self._execute_commands()

    def _rescan_button_clicked(self, e):
        self.log_window.clear()
        self.print_version_text()
        self.refresh_device_combo()
        self.print_sanitycheck()

    def refresh_device_combo(self):
        """ Replace the serial ports with the currently-deleted ones """
        self.device_combo.clear()
        self.device_combo.addItems(self.firmware_updater.get_serial_port_strings())

    def closeEvent(self, e):
        """ Save our window position and selected firmware for next time """
        self.settings.setValue("pos", self.pos())
        self.settings.setValue("firmwareName", self.firmware_combo.currentText())
        e.accept()


if __name__ == '__main__':
    app = QApplication([])
    window = FirmwareUpdaterMainWindow()
    window.show()
    sys.exit(app.exec())
