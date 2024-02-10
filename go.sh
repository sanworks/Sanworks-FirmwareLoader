#!/bin/bash

# Check if there are updates to this repository
git pull

# Check if venv directory exists; create if it doesn't...
if [ ! -d "venv" ]; then
    echo Creating Virtual Environment...
    python3 -m venv venv
fi

# ...but Bail if it still doesn't exist...
if [ ! -d "venv" ]; then
    echo FAILED to CREATE Virtual Environment!
    exit 1
fi

# Activate the virtual environment
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo FAILED to ENTER Virtual Environment!
    exit 1
fi

# Update requirements
pip install --upgrade -r requirements.txt

# Run the Firmware Updater GUI
python3 sanfw.py

# Deactivate the virtual environment
deactivate
