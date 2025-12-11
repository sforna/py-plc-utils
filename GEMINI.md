# py-plc-utils Context

## Project Overview
`py-plc-utils` is a collection of Python-based interactive CLI tools designed for exploring and troubleshooting industrial PLC communications. It supports three major protocols:
- **Siemens S7** (via `snap7`)
- **Modbus TCP** (via `pymodbus`)
- **OPC UA** (via `asyncua`)

The tools are intended for field usage, manual data collection, and diagnostics. While the documentation (`README.md`, `AGENTS.md`) is in English, the interactive prompts and comments within the source code (e.g., `src/plc_opcua_reader.py`) are primarily in **Italian**.

## Environment & Setup
The project relies on a standard Python virtual environment.

### Prerequisites
- Python 3.10+
- System libraries for `python-snap7` (platform dependent).

### Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
# Note: Ensure requirements.txt exists (referenced in docs) or install manually:
# pip install python-snap7 pymodbus asyncua python-dotenv
pip install -r requirements.txt
```

## Usage
Each protocol has its own dedicated script in the `src/` directory.

| Protocol | Command | Description |
| :--- | :--- | :--- |
| **Siemens S7** | `python src/plc_s7_reader.py` | Connects to S7 PLCs. Features rack/slot scanning and data block parsing. |
| **Modbus TCP** | `python src/plc_modbus_reader.py` | Reads coils, inputs, and registers. Includes basic type parsing. |
| **OPC UA** | `python src/plc_opcua_reader.py` | Connects to OPC UA servers. Supports hierarchical browsing and snapshot exports. |

## Development Conventions

### Code Style
- **Formatting:** Follows PEP 8 (4-space indentation).
- **Naming:** Snake_case for functions/variables, ALL_CAPS for constants.
- **Language:** Source code strings/prompts are in **Italian**. Documentation is in **English**.

### Testing
- **Manual Testing:** Primary method. Run the scripts against real or simulated hardware.
- **Automated Testing:** `pytest` is recommended for new features (place in `tests/`).
- **Pre-commit:** Run `python -m compileall src` to check for syntax errors.

## Key Files
- `src/plc_opcua_reader.py`: OPC UA client. Handles connection, node browsing, and type parsing.
- `src/plc_s7_reader.py`: Siemens S7 client.
- `src/plc_modbus_reader.py`: Modbus TCP client.
- `AGENTS.md`: Detailed guidelines for AI agents and contributors regarding style and workflow.
- `print_all_nodes.py`: Likely a utility script for OPC UA node enumeration.
- `README.md`: General user documentation.
