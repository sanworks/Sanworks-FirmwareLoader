@echo off
setlocal

rem Check if there are updates to this repository
git pull

rem Check if venv directory exists; create if it doesn't...
if not exist venv (
    echo Creating Virtual Environment...
    python -m venv venv
)

rem ...but Bail if it still doesn't exist...
if not exist venv (
    echo FAILED to CREATE Virtual Environment!
    exit /b 1
)

rem Activate the virtual environment
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo FAILED to ENTER Virtual Environment!
    exit /b 1
)

rem Update requirements
python -m pip install --upgrade pip
pip install --upgrade -r requirements.txt

rem Run the Firmware Updater GUI
python sanfw.py

rem Deactivate the virtual environment
deactivate

endlocal
exit /b 0
