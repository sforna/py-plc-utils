# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

py-plc-utils is a Python utility library for reading and writing data from industrial PLCs (Programmable Logic Controllers). The project supports three main protocols:
- **Siemens S7** communication using the python-snap7 library
- **Modbus TCP** communication using the pymodbus library
- **OPC UA** communication using the asyncua library

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

## Dependencies

- **python-snap7==2.0.2**: Siemens S7 protocol communication
- **python-dotenv==1.1.1**: Environment variable management (.env file support)
- **pymodbus==3.11.3**: Modbus TCP protocol communication
- **asyncua==1.1.8**: OPC UA protocol communication

## Architecture

The project consists of three main modules located in the `src/` directory:

### plc_modbus_reader.py
Handles Modbus TCP communication with industrial PLCs. Key functions:
- `connect_to_plc()`: Establishes TCP connection to Modbus PLC
- `read_coils()`, `read_discrete_inputs()`: Digital input/output operations
- `read_holding_registers()`, `read_input_registers()`: Analog data operations
- `parse_register_data()`: Converts raw register data to typed values (int16, uint16, int32, uint32, float32, string)

Supports all standard Modbus data types and register orders (big-endian/little-endian for 32-bit values).

### plc_s7_reader.py
Handles Siemens S7 protocol communication using snap7. Key functions:
- `connect_to_plc()`: Connects to S7 PLC via IP, rack, and slot parameters
- `scan_plc_network()`: Scans all rack/slot combinations (0-7 for rack, 0-10 for slot) to discover online PLCs
- `read_plc_data()`: Reads data blocks (DB) from S7 PLC memory
- `parse_data()`: Interprets raw bytes as bool, int, real, udint, or string data types
- `get_string()`: Custom string parsing for S7 string format

The module offers two connection modes: direct connection with known rack/slot parameters, or automatic scanning to discover accessible PLCs on the network.

### plc_opcua_reader.py
Handles OPC UA communication using asyncua. Key functions:
- `connect_to_opcua_server()`: Establishes connection to OPC UA endpoint
- `disconnect_from_server()`: Properly closes OPC UA connection and event loop
- `read_node_value()`: Reads value from a specific node ID
- `read_node_data_type()`: Retrieves data type information for a node
- `resolve_node_reference()`: Converts various node reference formats into Node objects
- `browse_nodes()`: Navigates OPC UA namespace hierarchy
- `export_to_json()`, `export_to_csv()`: Export collected data to files

Uses asyncio with synchronous wrapper functions for interactive CLI usage. Supports browsing the namespace tree and exporting snapshots of node values.

All modules provide interactive command-line interfaces for manual PLC data exploration and testing.

## Code Conventions

- Italian language is used for user-facing messages and prompts
- Error handling includes both exception catching and protocol-specific error checking
- Connection parameters are collected interactively via input prompts (with .env file support via python-dotenv)
- Data parsing includes proper type conversion and validation
- All modules follow similar patterns: connect → read → parse → display
- OPC UA module uses asyncio but wraps async operations in synchronous helper functions for CLI compatibility
- Network scanning features (S7 rack/slot scanner) test connections systematically and report progress