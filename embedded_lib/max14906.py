# driver for max chips on ROX-ECU board
from digitalio import DigitalInOut
import busio

DEBUG = False  # set to True  for verbose output


# ----------------- Max registers


class REGISTERS:
    # Output and LED configuration
    SET_OUT = 0x00
    SET_LED = 0x01

    # Fault and status information
    DOI_LEVEL = 0x02
    INTERRUPT = 0x03
    OVR_LD_CH_F = 0x04
    OPN_WIR_CH_F = 0x05
    SHT_VDD_CH_F = 0x06
    GLOBAL_ERR = 0x07

    # Configuration and control
    OPN_WR_EN = 0x08
    SHT_VDD_EN = 0x09
    CONFIG1 = 0x0A
    CONFIG2 = 0x0B
    CONFIG_DI = 0x0C
    CONFIG_DO = 0x0D
    CURR_LIM = 0x0E

    # Miscellaneous and reserved
    MASK = 0x0F

    @classmethod
    def get_registers(cls) -> list[tuple[str, int]]:
        """(name,value) pairs of all register values in the class"""
        return [
            (attr, getattr(cls, attr))
            for attr in dir(cls)
            if not attr.startswith("__") and not callable(getattr(cls, attr))
        ]

    @classmethod
    def get_name(cls, value: int) -> str | int:
        """get the name of a register from its value"""
        for attr in dir(cls):
            if not attr.startswith("__") and not callable(getattr(cls, attr)):
                if getattr(cls, attr) == value:
                    return attr
        return value


def decode_global_err(register_value: int) -> list:
    """
    Decode the GlobalErr register value into human-readable errors.

    Args:
    register_value (int): The 8-bit value of the GlobalErr register.

    Returns:
    list of str: Descriptions of the active errors.
    """
    error_descriptions = {
        7: "Watchdog Error: SPI or SYNCH watchdog timeout detected.",
        6: "Loss of Ground: Loss of ground fault detected.",
        5: "Thermal Shutdown: The device has entered thermal shutdown.",
        4: "VDD Under-Voltage: VDD has fallen below the under-voltage lock-out threshold.",
        3: "VDD Warning: VDD is below the warning threshold.",
        2: "VDD Low: VDD is significantly below the nominal operating level.",
        1: "V5 Under-Voltage: V5 has fallen below its under-voltage lock-out threshold.",
        0: "Internal Supply Voltage Low: Internal supply voltage is below threshold.",
    }
    active_errors = []

    for bit in range(8):  # Check each bit from 0 to 7
        if register_value & (1 << bit):  # If the bit is set
            active_errors.append(error_descriptions[bit])

    return active_errors


class Max14906:
    """driver for MAX14906 chips on ROX-ECU board"""

    def __init__(
        self,
        spi: busio.SPI,
        cs: DigitalInOut,
        d_pins: list[DigitalInOut],
        chip_address: int = 0,
    ):
        self.chip_address = chip_address
        self._spi = spi
        self._cs = cs

        self.d_pins = d_pins

        for p in self.d_pins:
            p.switch_to_output(False)

        self.get_global_error()  # clear the global error register

        # set leds to internal operation
        self.set_bit(REGISTERS.CONFIG1, 1, False)

        # write default values (partially)
        self.write_register(REGISTERS.SET_OUT, 0x00)
        self.write_register(REGISTERS.CONFIG_DO, 0x00)

    def set_bit(self, reg: int, bit: int, value: bool) -> bytearray:
        """set a single bit in a register"""
        data = self.read_register(reg)[1]
        data = data | (1 << bit) if value else data & ~(1 << bit)

        return self.write_register(reg, data)

    def switch_to_output(self, d_pin_nr: int, value: bool) -> None:
        """switch a D pin to output and set value"""
        self.d_pins[d_pin_nr].switch_to_output(value)

        # clear SetDi bit
        self.set_bit(REGISTERS.SET_OUT, d_pin_nr + 4, False)

    def switch_to_input(self, d_pin_nr: int) -> None:
        """switch a D pin to input"""
        self.d_pins[d_pin_nr].switch_to_input()

        # set SetDi bit
        self.set_bit(REGISTERS.SET_OUT, d_pin_nr + 4, True)

    def read_register(self, reg: int) -> bytearray:
        """single cycle read"""
        mosi_byte = (self.chip_address << 6) | (reg << 1) & 0xFE

        data_out = bytes([mosi_byte, 0x00])
        data_in = bytearray(2)

        self._cs.value = False
        self._spi.write_readinto(data_out, data_in)
        self._cs.value = True

        if DEBUG:
            print(
                f"read [{reg:02X}]({REGISTERS.get_name(reg)}) > {data_out.hex(' ')} , < {data_in.hex(' ')} ({data_in[1]:08b})"
            )

        return data_in

    def write_register(self, reg: int, data_byte: int) -> bytearray:
        """single cycle write, write a single byte to a register, returns the data read back"""

        mosi_byte = (self.chip_address << 6) | (reg << 1) | 0x1

        data_out = bytes([mosi_byte, data_byte])
        data_in = bytearray(2)

        self._cs.value = False
        self._spi.write_readinto(data_out, data_in)
        self._cs.value = True

        if DEBUG:
            print(
                f"write [{reg:02X}]({REGISTERS.get_name(reg)}) {data_out.hex(' ')} , < {data_in.hex(' ')}"
            )

        return data_in

    def get_global_error(self) -> int:
        """get the global error register"""
        return self.read_register(REGISTERS.GLOBAL_ERR)[1]

    def print_registers(self) -> None:
        """print all register values"""
        global DEBUG

        debug_bck = DEBUG
        DEBUG = True

        for name, reg in REGISTERS.get_registers():
            self.read_register(reg)

        DEBUG = debug_bck
