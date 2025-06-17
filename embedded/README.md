# ROX ICU Embedded Development

This directory contains CircuitPython firmware for the ROX ICU device.

## Development Environment

**Option 1: Virtual Environment**
```bash
# From project root
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

**Option 2: VS Code DevContainer**
Open repository in DevContainer for pre-configured environment.

## Device Management Commands

All embedded development uses `invoke` tasks in this directory:

```bash
cd embedded/
invoke -l  # List all available commands
```

### Available Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `invoke find-device` | Locate CIRCUITPY mount point | `invoke find-device` |
| `invoke install-deps` | Install CircuitPython packages | `invoke install-deps` |
| `invoke sync-lib` | Sync code to device | `invoke sync-lib` |
| `invoke init` | Full setup: deps + sync + hello world | `invoke init` |

## Development Workflow

1. **Find your device:**
   ```bash
   invoke find-device
   # Output: Device found at /media/user/CIRCUITPY
   ```

2. **Install dependencies:**
   ```bash
   invoke install-deps
   # Installs packages from cpy_requirements.txt
   ```

3. **Deploy your code:**
   ```bash
   invoke sync-lib
   # Syncs lib/ folder to device
   ```

4. **Quick setup for new device:**
   ```bash
   invoke init
   # Does install-deps + sync-lib + copies hello example
   ```

## Examples and Learning

Start with examples in `examples/`:
- `101_hello_icu.py` - Basic ICU board interaction
- `102_hello_can.py` - CAN bus communication
- `201_max_outputs.py` - Digital output control
- `202_max_inputs.py` - Digital input reading
- `301_board_demo.py` - Complete board demonstration

## Running Code on Device

### Method 1: Copy to main.py
```bash
cp examples/101_hello_icu.py /media/user/CIRCUITPY/main.py
```

### Method 2: Direct execution
```bash
# Find device port first
sudo dmesg | grep tty

# Run with mpremote (recommended)
mpremote /dev/ttyACM0 run examples/101_hello_icu.py

# Or with ampy (set AMPY_PORT environment variable)
export AMPY_PORT=/dev/ttyACM0
ampy run examples/101_hello_icu.py
```

## Hardware Setup

1. **Connect ICU device via USB**
2. **Put device in bootloader mode** (double-click reset button)
3. **Install CircuitPython firmware** (`.uf2` file)
4. **Device should mount as CIRCUITPY drive**

## Device Mounting

Most Linux distributions automatically mount the device under `/media/<user>/CIRCUITPY`.

If not automatically mounted, use the provided script:
```bash
../mount_device.sh
```

## Troubleshooting

### Device not found
```bash
invoke find-device
# If not found, try manual mount:
../mount_device.sh
```


### REPL access
```bash
mpremote /dev/ttyACM0 repl
```

### Common Issues

1. **Permission denied accessing device:**
   ```bash
   # Add user to dialout group
   sudo usermod -a -G dialout $USER
   # Log out and back in
   ```

2. **Device not mounting:**
   - Try different USB cable
   - Check if device is in bootloader mode
   - Use `lsusb` to verify device is detected

3. **CircuitPython not responding:**
   - Press reset button
   - Check for syntax errors in `main.py`
   - Check if `code.py` is present next to `main.py`
   - Use REPL to debug interactively

4. **Filesystem corruption**
   - Connect to device REPL and run:
   - `import storage; storage.erase_filesystem()`


## File Structure

```
embedded/
├── lib/                    # Shared libraries (symlinked to ../src/rox_icu/firmware/)
│   ├── bit_ops.py         # Bit manipulation utilities
│   ├── can_protocol.py    # CAN bus protocol implementation
│   ├── icu_board.py       # Board abstraction layer
│   └── max14906.py        # MAX14906 I/O driver
├── examples/              # Example programs
├── remote_io/             # Main Remote I/O firmware
│   ├── main.py           # Remote I/O application
│   └── settings.toml     # Configuration
├── benchmarks/            # Performance testing
├── cpy_requirements.txt   # CircuitPython dependencies
└── tasks.py              # Invoke task definitions
```

## Code Organization

### Shared Libraries
The `lib/` directory contains symlinks to `../src/rox_icu/firmware/` to share code between embedded and PC environments. This allows:
- Running embedded code on PC using mocks
- Maintaining single source of truth for protocol implementation
- Testing embedded logic without hardware

### Main Applications
- `remote_io/main.py` - Primary Remote I/O firmware
- `examples/` - Learning and testing examples
- `benchmarks/` - Performance measurement tools

## Development Tips

1. **Use examples to learn** - Start with simple examples before complex applications
2. **Test with mocks first** - Use PC-side mocks for rapid development
3. **Validate on hardware** - Always test final code on actual device
4. **Monitor CAN traffic** - Use `candump vcan0` or `icu monitor` to debug communication
5. **Keep backups** - Save working code before major changes
