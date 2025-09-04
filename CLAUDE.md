# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

py-plc-utils is a Python utility library for reading and writing data from industrial PLCs (Programmable Logic Controllers). The project supports two main protocols:
- **Siemens S7** communication using the python-snap7 library
- **Modbus TCP** communication using the pymodbus library

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
```

## Dependencies

- **python-snap7==2.0.2**: Siemens S7 protocol communication
- **python-dotenv==1.1.1**: Environment variable management
- **pymodbus==3.11.1**: Modbus TCP protocol communication

## Architecture

The project consists of two main modules located in the `src/` directory:

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
- `read_plc_data()`: Reads data blocks (DB) from S7 PLC memory
- `parse_data()`: Interprets raw bytes as bool, int, real, udint, or string data types
- `get_string()`: Custom string parsing for S7 string format

Both modules provide interactive command-line interfaces for manual PLC data exploration and testing.

## Code Conventions

- Italian language is used for user-facing messages and prompts
- Error handling includes both exception catching and Modbus-specific error checking
- Connection parameters are collected interactively via input prompts
- Data parsing includes proper type conversion and validation
- Both modules follow similar patterns: connect → read → parse → display