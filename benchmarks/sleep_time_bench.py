import gc
import board
import time
import digitalio
from micropython import const

gc.disable()

# Constants
SLEEP_TIME = const(0.01)  # seconds
DISPLAY_INTERVAL = const(10)  # cycles
BIN_SIZE = const(0.1)  # milliseconds (100 microseconds)
NANOSECONDS_PER_BIN = const(100_000)  # 100,000 nanoseconds per bin
MAX_ASTERISKS = const(50)  # Maximum number of asterisks for histogram display

# LED setup
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Initialize variables
histogram = {}
iteration = 0


def toggle_led():
    led.value = not led.value


def update_histogram(diff_ns):
    bin_key = diff_ns // NANOSECONDS_PER_BIN
    histogram[bin_key] = histogram.get(bin_key, 0) + 1


def display_histogram():
    if not histogram:
        print("Histogram is empty.")
        return

    max_count = max(histogram.values())
    print("\nHistogram (bin size: 0.1 ms):")
    for bin_key in sorted(histogram.keys()):
        count = histogram[bin_key]
        asterisks = round((count / max_count) * MAX_ASTERISKS)
        bin_start = bin_key * BIN_SIZE
        print(f"{bin_start:.1f} ms  {'*' * asterisks:<{MAX_ASTERISKS}} {count}")
    print()


def main():
    global iteration

    while True:
        iteration += 1

        start_time = time.monotonic_ns()
        time.sleep(SLEEP_TIME)
        end_time = time.monotonic_ns()

        diff_ns = end_time - start_time

        update_histogram(diff_ns)

        if iteration % DISPLAY_INTERVAL == 0:
            display_histogram()
            toggle_led()

        print(f"\r{iteration:4}: {end_time:10} - {diff_ns/1e6:.3f}ms     ", end="")

        gc.collect()


if __name__ == "__main__":
    main()
