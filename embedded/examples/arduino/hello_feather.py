import time
import board
import digitalio
import neopixel

# Initialize the onboard LED
led = digitalio.DigitalInOut(board.D13)
led.direction = digitalio.Direction.OUTPUT


# Initialize the onboard NeoPixel
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixel.brightness = 0.3  # Adjust brightness as needed

counter = 0

while True:
    # Toggle the onboard LED
    led.value = not led.value

    # Toggle the NeoPixel between green and off
    if pixel[0] == (0, 0, 0):
        pixel[0] = (0, 255, 0)  # Green
    else:
        pixel[0] = (0, 0, 0)    # Off

    # Print the counter
    print(f"Counter: {counter}")
    counter += 1

    time.sleep(1)  # Delay for 1 second
