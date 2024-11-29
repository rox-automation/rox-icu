# example of time measurement
import gc
import time

for _ in range(50):
    t_start = time.monotonic_ns()
    time.sleep(0.001)
    t_end = time.monotonic_ns()
    t_elapsed = (t_end - t_start) / 1e6
    error = abs(t_elapsed - 1)

    print(f"elapsed: {t_elapsed:.3f} ms (error: {error:.1%})")
    gc.collect()
