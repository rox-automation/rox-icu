# SPDX-FileCopyrightText: 2020 anecdata for Adafruit Industries
# SPDX-FileCopyrightText: 2021 Neradoc for Adafruit Industries
# SPDX-FileCopyrightText: 2021-2023 Kattni Rembor for Adafruit Industries
# SPDX-FileCopyrightText: 2023 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# CircuitPython Essentials Pin Map Script
# This script generates a list of all the pins available on the board,
# along with their corresponding aliases.

import microcontroller
import board

# Initialize a list to hold pin mappings
mapped_pins = []

# Iterate over every attribute in the microcontroller.pin module
for pin_name in dir(microcontroller.pin):
    pin_obj = getattr(microcontroller.pin, pin_name)
    # Check if the attribute is an instance of a Pin
    if isinstance(pin_obj, microcontroller.Pin):
        # Temporarily store aliases for this pin
        pin_aliases = []
        # Check each attribute in the board module
        for alias in dir(board):
            if getattr(board, alias) is pin_obj:
                # If the board attribute is the same as the pin, add it to the aliases
                pin_aliases.append(f"board.{alias}")
        # If there are any aliases, append the original GPIO name and the aliases to the list
        if pin_aliases:
            pin_aliases.append(f"({str(pin_name)})")
            mapped_pins.append(" ".join(pin_aliases))

# Print each pin and its aliases, sorted for readability
for pin_info in sorted(mapped_pins):
    print(pin_info)
