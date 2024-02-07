#!/bin/bash

git pull

# Check if venv directory exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Update requirements
pip install --upgrade -r requirements.txt

# Run the python script
python3 sanfw.py

# Deactivate the virtual environment
deactivate
