# driver for max chips on ROX-ECU board
from digitalio import DigitalInOut, Direction
import busio
import ecu_board as board

DEBUG = False  # set to True  for verbose output


SPI = busio.SPI(board.SCK, board.MOSI, board.MISO)
while not SPI.try_lock():
    pass

print("spi locked")
SPI.configure(baudrate=500_000, phase=0, polarity=0)

# other pins

CS = DigitalInOut(board.MAX_CS)  # toggle to start a new transaction
CS.direction = Direction.OUTPUT
CS.value = True

SYNCH = DigitalInOut(board.MAX_SYNCH)
SYNCH.direction = Direction.OUTPUT
SYNCH.value = True

NREADY = DigitalInOut(board.MAX_NREADY)
NREADY.direction = Direction.INPUT
print(f"NREADY: {NREADY.value}")

CRC_ENABLE = DigitalInOut(board.MAX_CRCEN)
CRC_ENABLE.direction = Direction.OUTPUT
CRC_ENABLE.value = False
print(f"CRC_ENABLE: {CRC_ENABLE.value}")


ENABLE = DigitalInOut(board.MAX_ENABLE)
ENABLE.direction = Direction.OUTPUT
ENABLE.value = False

NFAULT_M1 = DigitalInOut(board.MAX1_NFAULT)
NFAULT_M1.direction = Direction.INPUT
print(f"NFAULT_M1: {NFAULT_M1.value}")

NFAULT_M2 = DigitalInOut(board.MAX2_NFAULT)
NFAULT_M2.direction = Direction.INPUT
print(f"NFAULT_M2: {NFAULT_M2.value}")


# d-pins
D_PINS = [DigitalInOut(pin) for pin in board.D_PINS]
for p in D_PINS:
    p.switch_to_output(False)

# map d-pins to names on the board
input_to_d_pins = dict(zip(["D5", "D6", "D7", "D8", "D1", "D2", "D3", "D4"], D_PINS))


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


def read_register(
    reg: int,
    chip_address: int = 0,
) -> bytearray:
    """single cycle read"""
    mosi_byte = (chip_address << 6) | (reg << 1) & 0xFE

    data_out = bytes([mosi_byte, 0x00])
    data_in = bytearray(2)

    CS.value = False
    SPI.write_readinto(data_out, data_in)
    CS.value = True

    if DEBUG:
        print(
            f"read [{reg:02X}]({REGISTERS.get_name(reg)}) > {data_out.hex(' ')} , < {data_in.hex(' ')} ({data_in[1]:08b})"
        )

    return data_in


def write_register(reg: int, data_byte: int, chip_address: int = 0) -> bytearray:
    """single cycle write, write a single byte to a register, returns the data read back"""
    mosi_byte = (chip_address << 6) | (reg << 1) | 0x1

    data_out = bytes([mosi_byte, data_byte])
    data_in = bytearray(2)

    CS.value = False
    SPI.write_readinto(data_out, data_in)
    CS.value = True

    if DEBUG:
        print(
            f"write [{reg:02X}]({REGISTERS.get_name(reg)}) {data_out.hex(' ')} , < {data_in.hex(' ')}"
        )

    return data_in


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

    def __init__(self, chip_address: int = 0):
        self.chip_address = chip_address

        if chip_address == 0:
            self.d_pins = D_PINS[:4]
            self.nfault = NFAULT_M1
            self.nvddok = DigitalInOut(board.MAX1_NVDDOK)
        elif chip_address == 1:
            self.d_pins = D_PINS[4:]
            self.nfault = NFAULT_M2
            self.nvddok = DigitalInOut(board.MAX2_NVDDOK)
        else:
            raise ValueError(f"invalid chip address {chip_address}")

        # check fault lines
        assert not self.nvddok.value, f"NVDDOK line is high on chip {chip_address}"

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
        return read_register(reg, self.chip_address)

    def write_register(self, reg: int, data_byte: int) -> bytearray:
        """single cycle write, write a single byte to a register, returns the data read back"""
        return write_register(reg, data_byte, self.chip_address)

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
