# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

py-plc-utils is a Python utility library for reading and writing data from industrial PLCs (Programmable Logic Controllers). The project consists of three standalone interactive CLI tools, each supporting a different industrial protocol:
- **Siemens S7** communication using the python-snap7 library
- **Modbus TCP** communication using the pymodbus library
- **OPC UA** communication using the asyncua library

All three modules are independent, self-contained programs designed for field diagnostics and manual data exploration. They share similar architectural patterns but operate on completely different protocols.

## Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Applications
```bash
# Run Modbus TCP client
python src/plc_modbus_reader.py

# Run Siemens S7 client
python src/plc_s7_reader.py

# Run OPC UA client
python src/plc_opcua_reader.py
```

### Testing
```bash
# Check for syntax errors before committing
python -m compileall src
```

### Running with Timeouts (for testing)
```bash
# Run OPC UA client with timeout (useful when testing connection issues)
timeout 10 python src/plc_opcua_reader.py
timeout 15 python src/plc_opcua_reader.py
timeout 30 python src/plc_opcua_reader.py
```

## Architecture

The project consists of three main modules located in the `src/` directory. Each module is a standalone interactive CLI program with no shared code between them.

### Common Architectural Pattern

All three readers follow the same general architecture:
1. **Connection phase**: Prompt user for connection parameters (IP, port, rack/slot, endpoint URL)
2. **Interactive menu**: Present numbered options for different operations
3. **Read operations**: Execute protocol-specific reads with error handling
4. **Parse and display**: Convert raw protocol data to typed values and display to user
5. **Optional export**: Some modules support exporting data to timestamped files

### plc_modbus_reader.py - Modbus TCP Reader

Handles Modbus TCP communication. Key architectural points:
- Uses pymodbus `ModbusTcpClient` for connectivity
- Supports 4 Modbus data areas: coils, discrete inputs, holding registers, input registers
- Register parsing supports multiple data types with configurable endianness
- **Parse function**: `parse_register_data(registers, data_type, register_order='big')` handles int16, uint16, int32, uint32, float32, and string conversions
- Multi-register values (32-bit) support both big-endian and little-endian byte order

### plc_s7_reader.py - Siemens S7 Reader

Handles Siemens S7 protocol using snap7. Key architectural points:
- **Connection requires 3 parameters**: IP address, rack number (0-7), and slot number (0-10)
- **Two connection modes**:
  - Direct connection: User provides known rack/slot values
  - Scanner mode: `scan_plc_network()` systematically tests all 88 rack/slot combinations (8 racks × 11 slots)
- Reads from data blocks (DBs) in PLC memory with offset-based addressing
- **Custom string parsing**: S7 strings have special format requiring `get_string()` helper instead of standard snap7 utilities
- Scanner mode distinguishes between "PLC online with DB accessible" vs "PLC connected but DB not accessible"

### plc_opcua_reader.py - OPC UA Navigator

Handles OPC UA communication using asyncua. Key architectural points:
- **Async/sync hybrid architecture**: Uses asyncio internally but wraps all async operations in synchronous helper functions for CLI compatibility
- Each synchronous function creates an async inner function and runs it via `loop.run_until_complete()`
- **Connection lifecycle**: `connect_to_opcua_server()` creates event loop and client, `disconnect_from_server()` properly cleans up both
- **Node reference resolution**: `resolve_node_reference()` handles multiple node ID formats (string references like "objects"/"root", numeric NodeIds, string NodeIds with namespace)
- **Three main operations**:
  1. Read single node value
  2. Interactive hierarchical navigation with `interactive_node_navigation()`
  3. Export all variables under a node to timestamped file with `export_variables_to_file()`
- **Data type reading**: Uses `read_data_type()` to get type NodeId, then reads browse name from type node to get human-readable type (Int16, Int32, Double, String, etc.)
- **Export format**: Generates timestamped text files with format: `variables_{node_fragment}_{timestamp}.txt`

## Code Conventions

- **Italian language**: All user-facing messages, prompts, and menu items are in Italian
- **Error handling**: Both exception catching and protocol-specific error checking (e.g., Modbus `isError()`)
- **Connection parameters**: Collected interactively via `input()` prompts (`.env` file support available via python-dotenv but not currently used)
- **Data type handling**: Document endianness, register width, and expected units inline when working with PLC data
- **Naming conventions**: Follow PEP 8 with snake_case for functions and ALL_CAPS for connection constants
- **OPC UA async pattern**: Always wrap async operations in synchronous helper functions that create async inner functions and run them with `loop.run_until_complete()`