# Sanworks-FirmwareLoader

A cross platform tool to load firmware binaries to Sanworks devices.

---

This repository includes:

- **Firmware Binaries**: Official public firmware releases for all products in the Sanworks open source neuroscience hardware ecosystem, including Pulse Pal, Bpod, and Bpod modules.

- `sanfw.py`, A **Python-based GUI** for loading / re-loading device firmware.

- `SanworksFirmwareLoader.m` A **MATLAB-based GUI** for loading / re-loading device firmware.
  - NOTE: This was copied from the `Bpod_Gen2` repository and likely needs some work to get working!

## Python: Running the Firmware Update GUI

### Typical Usage...
- Clone this repository
- Install a version of Python >= 3.7
- Run `go.bat` on Windows, or `go.sh` on Linux / Mac.  **This script will**:
  - `git pull` to get the latest firmware and code
  - create a Python virtual environment, `venv`, if one isn't already there
  - install `requirements.txt` into that virtual environment, if necessary
  - run the actual `sanfw.py` GUI

### With an IDE (e.g. PyCharm)...
In Theory:
- Open this folder in your IDE
- Set up a python interpreter
- Install `requirements.txt`
- Click the run button

In Practice: PyCharm will guide you through most of it with colorful alert bars...

## Python: Using the Firmware Update GUI
- Select your Firmware by family and version.
- Select your Device by serial port. Use the `RESCAN` button if you plug / unplug anything.
- Press the `LOAD` button to initiate the firmware update. This may take several minutes on some devices.


## MATLAB: Running the Firmware Update GUI
- Add this folder to your MATLAB path
- Run `SanworksFirmwareLoader` at the MATLAB prompt


## Firmware Sources
Each project has a separate repository, hosted under the https://github.com/sanworks namespace.


## Notes

Firmware files in this folder begin with stable versions as of 1 July, 2022, and include more recent updates.

If you need an earlier firmware version, it must be installed manually. Installation instructions are here:
https://sites.google.com/site/bpoddocumentation/firmware-update

Firmware updating for Teensy-powered Bpod Gen2 modules is powered by tycmd, an open source firmware loader application for Teensy.
More details at: https://github.com/Koromix/tytools

For Arduino, Adafruit and Sparkfun brand boards, firmware updating is powered by bossac.
More details at: https://github.com/shumatech/BOSSA
