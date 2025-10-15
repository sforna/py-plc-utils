# py-plc-utils

Utilities for exploring and interacting with industrial PLCs over Siemens S7, Modbus TCP, and OPC UA protocols. Each tool is an interactive Python CLI designed for quick diagnostics and manual data collection in the field.

## Features
- **Siemens S7 reader** with optional rack/slot scanner and helpers for parsing BOOL, INT, REAL, STRING, and UDINT data blocks.
- **Modbus TCP reader** that fetches coils, discrete inputs, holding registers, and input registers with basic parsing utilities.
- **OPC UA navigator** that connects to an endpoint, browses nodes, reads values, and exports snapshots.

## Getting Started
1. Install Python 3.10+ and the required system packages for `python-snap7`.
2. Clone the repository and create an isolated environment:
   ```bash
   git clone <repo-url>
   cd py-plc-utils
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Create a `.env` file with connection details such as PLC IPs, ports, and credentials (you can keep a redacted template as `.env.example` for teammates). The tools rely on `python-dotenv` to load these variables automatically.

## Usage
- **Siemens S7**
  ```bash
  python src/plc_s7_reader.py
  ```
  Choose between direct connection or automatic rack/slot scanning, then read data blocks by specifying offsets, types, and lengths.

- **Modbus TCP**
  ```bash
  python src/plc_modbus_reader.py
  ```
  Select coil/discrete/register reads, specify the address range, and optionally parse the returned registers (INT/UINT/REAL/STRING).

- **OPC UA**
  ```bash
  python src/plc_opcua_reader.py
  ```
  Connect to an OPC UA endpoint, browse the namespace, read node values, and export data to JSON/CSV when prompted.

## Development Workflow
- Run `python -m compileall src` before committing to catch syntax errors.
- Manual protocol testing is encouraged; include the command you ran and the simulated/real device in your PR notes.
- Refer to `AGENTS.md` for in-depth contributor guidelines on style, commits, and security practices.

## Troubleshooting
- Ensure the required ports (Modbus 502, S7 102, OPC UA per server config) are reachable from your network segment.
- When using the OPC UA client, verify certificates or security policies if the server requires them; update the `.env` with the correct URL.
- For Siemens S7 access errors, double-check rack/slot values or use the scanner mode to discover valid combinations.

## License
This project has not declared a license. Contact the maintainers before using it in production or distributing modified versions.
