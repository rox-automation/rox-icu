# ROX Integrated Control Unit (ICU)

![](assets/icu-board.webp)

ROX Integrated Control Unit (ICU) is a modern, open-source alternative to conventional PLCs, designed for demanding industrial applications. Based on the Adafruit Feather M4 CAN platform, this compact device integrates an automotive-grade microcontroller, digital I/O, analog inputs, and CAN interface into a single, robust package.

## Key Features

- **Wide operation range** 10V to 40V Operating Supply Range, 65V Tolerant
- **Industrial-Grade I/O:**
    - 8x configurable digital I/O channels (up to 40V and 1.2A per channel) with overcurrent protection and comprehensive diagnostics.
    - Per-Channel Configurability Enables Wide Range of Applications
        - Digital Output: High-Side (HS) Switch or Push-Pull (PP) Driver
        - Digital Input: Software Selectable Type 1 and 3, or Type 2
        - Current Limit Settable from 130mA to 1.2A
        - Independent Channel Powering
    - Fault Tolerant with Built-In Diagnostics
        - Voltage Supply Monitoring and Short-to-VDD Detection
        - Open-Wire/Open-Load Detection
        - Thermal Shutdown Protection, Watchdog Timer etc.
    - 2x analog input, 0..10V range, including reference voltage generator.
- **Connectivity:** Pass-through CAN connection for flexible integration.
- **Powerful Processing:** Features a 120MHz Cortex M4 processor with floating-point support, 512KB Flash, and 192KB RAM.
- **Compact Design:** Measures 96 x 57 mm, only slightly larger than a credit card.
- **Environmental Durability:** IP67 rated and shock-resistant, suitable for harsh industrial environments and mobile machinery.
- **Flexible Programming:** Compatible with Arduino, CircuitPython, C/C++ and Rust
- **Open Source:** Fully open-source design allows for customization and adaptation.

The ROX ICU is designed for decentralized control in mobile machinery and as a PLC replacement in challenging environments. It combines the accessibility of the Feather ecosystem with industrial-grade capabilities, offering a versatile solution for modern industrial control applications.

## Quick Start

**Requirements:** Python 3.11+ on Linux (Windows users should use WSL)

### 1. Development Environment Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install package with development dependencies
pip install -e .[dev]
```

### 2. Choose Your Development Path

#### 🔧 Embedded Development
For firmware development on the CircuitPython device:

```bash
cd embedded/
invoke find-device      # Locate mounted device
invoke init            # Install dependencies and hello world
```

📖 **[Complete Embedded Development Guide →](embedded/README.md)**

#### 💻 PC Software Development
For Python driver development and testing:

1. **Setup Virtual CAN** (Linux)
   ```bash
   sudo modprobe vcan
   sudo ip link add dev vcan0 type vcan
   sudo ip link set up vcan0
   ```

2. **Test with Mock**
   ```bash
   # Run mock device
   icu mock --node-id 1 --channel vcan0

   # Monitor in another terminal
   icu monitor
   ```


## PC Software Development

### Installation & Setup

```bash
# Virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]

# Verify installation
icu --version
```

### CLI Commands

The `icu` command provides comprehensive device management and testing:

| Command | Description | Example |
|---------|-------------|---------|
| `icu monitor` | Monitor all CAN bus traffic | `icu monitor` |
| `icu mock` | Run mock device for testing | `icu mock --node-id 1 --channel vcan0` |
| `icu output` | Set device output state | `icu output --help` |
| `icu inspect` | Inspect specific device messages | `icu inspect --help` |
| `icu clear-errors` | Clear device error states | `icu clear-errors --help` |
| `icu command` | Send raw numeric commands | `icu command --help` |
| `icu info` | Show package information | `icu info` |

### Mock Testing Framework

The mock framework allows running embedded firmware on PC for development and testing:

1. **Setup virtual CAN:**
   ```bash
   # Linux setup
   sudo modprobe vcan
   sudo ip link add dev vcan0 type vcan
   sudo ip link set up vcan0
   ```

2. **Run mock device:**
   ```bash
   icu mock --node-id 1 --channel vcan0
   ```

3. **Monitor traffic:**
   ```bash
   # In another terminal
   icu monitor

   # Or use candump for raw CAN
   candump vcan0
   ```

4. **Interact with mock:**
   ```bash
   # Set outputs
   icu output --node-id 1 --value 0xFF

   # Monitor specific device
   icu inspect --node-id 1
   ```

### Development Workflow

1. **Write tests first** (following TDD approach)
2. **Use mocks for hardware-less development**
3. **Test with real hardware when available**
4. **Run code quality checks:**
   ```bash
   ruff check --fix
   ruff format
   mypy src
   pylint -E src tests
   ```

5. **Run test suite:**
   ```bash
   pytest --cov=src --cov-report term-missing tests
   ```

### Examples

PC-side examples in `examples/`:
- `cycle_outputs.py` - Cycle through output states
- `rio_wait_and_toggle.py` - Remote I/O demonstration

Advanced examples in `src/rox_icu/examples/`:
- `wait_and_toggle.py` - Async I/O patterns

## Hardware Reference

### Pin Mapping

```
board.A0 board.D14 (PA02)
board.A1 board.D15 (PA05)
board.A2 board.D16 (PB08)
board.A3 board.D17 (PB09)
board.A4 board.D18 (PA04)
board.A5 board.D19 (PA06)
board.BATTERY board.VOLTAGE_MONITOR (PB00)
board.BOOST_ENABLE (PB13)
board.CAN_RX (PB15)
board.CAN_STANDBY (PB12)
board.CAN_TX (PB14)
board.D0 board.RX (PB17)
board.D1 board.TX (PB16)
board.D10 (PA20)
board.D11 (PA21)
board.D12 (PA22)
board.D13 board.LED (PA23)
board.D23 board.MISO (PB22)
board.D24 board.MOSI (PB23)
board.D25 board.SCK (PA17)
board.D4 (PA14)
board.D5 (PA16)
board.D6 (PA18)
board.D9 (PA19)
board.NEOPIXEL (PB02)
board.NEOPIXEL_POWER (PB03)
board.SCL (PA13)
board.SDA (PA12)
```


## Contributing & Development

### Docker Development Stack

For full development environment with MQTT and monitoring:
```bash
docker-compose up -d
```

### Code Quality

Before committing changes:
```bash
# Python code quality (required)
ruff check --fix
ruff format
mypy src
pylint -E src tests

# Run tests
pytest --cov=src --cov-report term-missing tests

# Or use invoke shortcuts
invoke lint
invoke test
invoke ci  # Run CI locally in Docker
```

### Repository Structure

```
├── embedded/           # CircuitPython firmware
│   ├── lib/           # Shared libraries (symlinked to src/)
│   ├── examples/      # Example programs
│   ├── remote_io/     # Main Remote I/O firmware
│   └── tasks.py       # Device management commands
├── src/rox_icu/       # Python package
│   ├── firmware/      # Shared firmware code
│   ├── mocks/         # Hardware abstraction for PC testing
│   └── cli.py         # Command-line interface
├── tests/             # Test suite
├── examples/          # PC-side examples
└── pcb/              # Hardware design files
```

## Licenses

- **Software**: [MIT License](LICENSE)
- **Hardware**: [CC BY-SA 3.0](pcb/license.txt)
