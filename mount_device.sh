#!/bin/bash

USERNAME=$(whoami)  # Get the current username
MOUNT_POINT="/media/$USERNAME/CIRCUITPY"  # Target mount point
DEVICE=$(blkid -t LABEL="CIRCUITPY" -o device)  # Detect CIRCUITPY device

# Debugging output to ensure the variables are populated correctly
echo "Username: $USERNAME"
echo "Mount point: $MOUNT_POINT"
echo "Device: $DEVICE"

set -e  # Exit immediately on error

# Check if DEVICE is found
if [ -z "$DEVICE" ]; then
    echo "Error: CIRCUITPY device not found."
    exit 1
fi

# Create mount point if it doesn't exist
if [ ! -d "$MOUNT_POINT" ]; then
    echo "Creating mount point at $MOUNT_POINT"
    sudo mkdir -p "$MOUNT_POINT"
    sudo chown "$USERNAME":"$USERNAME" "$MOUNT_POINT"  # Change ownership
fi

# Mount the device
echo "Mounting $DEVICE to $MOUNT_POINT"
sudo mount -t vfat -o rw,uid=$(id -u "$USERNAME"),gid=$(id -g "$USERNAME"),fmask=0022,dmask=0022,flush "$DEVICE" "$MOUNT_POINT"

echo "Device successfully mounted to $MOUNT_POINT"
