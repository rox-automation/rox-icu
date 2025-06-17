# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ROX ICU (Integrated Control Unit) is a hybrid Python/CircuitPython project for industrial automation. It provides:
- **Embedded firmware** for Adafruit Feather M4 CAN-based hardware
- **PC driver software** for CAN bus communication
- **Mock framework** allowing embedded code to run on PC for testing

## Key Architecture

### Dual-Target Design
- **PC side**: Python 3.11+ package in `src/rox_icu/`
- **Embedded side**: CircuitPython code in `embedded/`
- **Shared code**: Libraries symlinked between PC and embedded environments

### Core Components
- **CAN Protocol**: Custom protocol for industrial I/O control
- **Remote I/O**: Digital I/O control over CAN bus using MAX14906 driver
- **Mock Framework**: Hardware abstraction layer allowing PC testing
- **CLI Tools**: `icu` command for device management and monitoring

## Development Commands

### Python Development
```bash
# Install dependencies
pip install -e .[dev]

# Code quality (MUST run after Python changes)
ruff check --fix
ruff format
mypy src
pylint -E src tests

# Testing
pytest --cov=src --cov-report term-missing tests

# Invoke tasks
invoke lint      # Static analysis
invoke test      # Run tests with coverage
invoke ci        # Run CI locally in Docker
invoke build_package  # Build package
```

### Embedded Development
```bash
# In embedded/ directory
invoke -l                    # List available commands
invoke find_device          # Locate CIRCUITPY mount point
invoke install_deps         # Install CircuitPython dependencies
invoke sync_lib             # Sync code to device
invoke init                 # Initialize device with demo code
```

### Hardware Tools
- `mpremote` - Manage CircuitPython devices
- `circup` - Install CircuitPython packages
- `ampy` - Alternative device management (set AMPY_PORT env var)

## Testing Strategy

### Mock-Based Testing
The project uses comprehensive mocks in `src/rox_icu/firmware/mocks/` to run embedded code on PC:
- `board`, `digitalio`, `canio` - Hardware abstraction mocks
- Run embedded firmware on PC: `icu mock --node-id 1 --channel vcan0`

### Test Structure
- `tests/` - Main test suite using pytest
- Async testing with `asyncio_default_fixture_loop_scope = "function"`
- Coverage reporting excludes CLI and mocks

## CAN Bus Development

### Virtual CAN Setup
```bash
# Create virtual CAN interface
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0

# Monitor CAN traffic
candump vcan0
```

### Protocol Testing
- Use `icu mock` to simulate devices
- Use `icu monitor` for real-time monitoring
- DBC files in `src/rox_icu/dbc/` for protocol definition

## File Organization

### Shared Libraries
These files exist in both locations (symlinked):
- `embedded/lib/` ↔ `src/rox_icu/firmware/`
- Common modules: `can_protocol.py`, `bit_ops.py`, `icu_board.py`

### Key Entry Points
- `src/rox_icu/cli.py` - Main CLI interface
- `embedded/remote_io/main.py` - Remote I/O firmware
- `src/rox_icu/mock.py` - PC mock runner

## Configuration

### Project Settings
- **Python version**: 3.11+ required
- **Build system**: setuptools with setuptools-scm
- **Dependencies**: Listed in `requirements.txt` and `.devcontainer/requirements-dev.txt`

### Development Environment
- DevContainer support with VS Code integration
- Docker compose stack for MQTT and monitoring
- Auto-mounting of CIRCUITPY device under `/media/<user>/CIRCUITPY`

## Special Development Notes

### Code Quality Requirements
- Always run `ruff check --fix` and `ruff format` after Python changes
- Type hints required (Python 3.10+ PEP 604 style)
- Pylint configuration excludes common embedded patterns

### Hardware Deployment
- Device auto-mounts as removable drive when connected
- Use `invoke sync_lib` to deploy code changes
- CircuitPython libraries managed via `circup`
- Clean filesystem: `import storage; storage.erase_filesystem()`

### Industrial Focus
- Wide voltage range support (10V-40V)
- 8 configurable digital I/O channels
- Built-in fault detection and diagnostics
- IP67 rated for harsh environments
