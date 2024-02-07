@echo off
setlocal

git pull

rem Check if venv directory exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

rem Activate the virtual environment
call venv\Scripts\activate.bat

rem Update requirements
pip install --upgrade -r requirements.txt

rem Run the python script
python sanfw.py

rem Deactivate the virtual environment
deactivate

endlocal
