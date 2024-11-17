def set_bit(value: int, bit: int) -> int:
    """set bit in value"""
    return value | (1 << bit)


def clear_bit(value: int, bit: int) -> int:
    """clear bit in value"""
    return value & ~(1 << bit)
