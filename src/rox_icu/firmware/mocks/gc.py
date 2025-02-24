# gc.py mock for CPython
import sys


def collect():
    """Simulate garbage collection"""
    print("gc.collect() called")
    # In CPython, garbage collection is automatic, but we can manually trigger it
    if "gc" in sys.modules:
        import gc

        gc.collect()


def enable():
    """Enable automatic garbage collection (does nothing in CPython)"""
    print("gc.enable() called")


def disable():
    """Disable automatic garbage collection (not recommended in CPython)"""
    print("gc.disable() called")


def mem_alloc():
    """Simulate reporting allocated memory (not available in CPython natively)"""
    return 0  # Dummy value, since CPython does not expose this


def mem_free():
    """Simulate reporting free memory (not available in CPython natively)"""
    return 0  # Dummy value, since CPython does not expose this


# Exported symbols to match CircuitPython's gc module
__all__ = ["collect", "enable", "disable", "mem_alloc", "mem_free"]
