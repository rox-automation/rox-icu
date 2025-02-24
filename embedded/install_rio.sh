#!/bin/bash

# Simple script to install remote IO firmware on ICU

# Find CIRCUITPY folder in /mnt/{username}/
CIRCUITPY=$(find /media -maxdepth 2 -type d -name CIRCUITPY 2>/dev/null)

# Check if the CIRCUITPY folder was found
if [[ -z "$CIRCUITPY" ]]; then
    echo "Error: CIRCUITPY folder not found."
    exit 1
fi

# Check if the CIRCUITPY folder is not empty
if [[ -z "$(ls -A "$CIRCUITPY" 2>/dev/null)" ]]; then
    echo "Error: CIRCUITPY folder is empty."
    exit 1
fi

echo "CIRCUITPY folder found at $CIRCUITPY"

echo "installing dependencies..."
circup install -r cpy_requirements.txt

echo "Syncing lib folder..."
rsync -avL --exclude '_*' lib/ "$CIRCUITPY/lib/"

echo "Copying main.py and settings.toml..."
rsync -avL remote_io/main.py remote_io/settings.toml "$CIRCUITPY/"

# remove code.py
rm -f "$CIRCUITPY/code.py"
