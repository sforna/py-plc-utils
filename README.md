# py-plc-utils

Utilities for exploring and interacting with industrial PLCs over Siemens S7, Modbus TCP, and OPC UA protocols. Each tool is an interactive Python CLI designed for quick diagnostics and manual data collection in the field.

## Features
- **Siemens S7 reader** with optional rack/slot scanner and helpers for parsing BOOL, INT, REAL, STRING, and UDINT data blocks.
- **Modbus TCP reader** that fetches coils, discrete inputs, holding registers, and input registers with basic parsing utilities.
- **OPC UA navigator** that connects to an endpoint, browses nodes, reads values, and exports snapshots.

## Getting Started
The project is managed with [uv](https://docs.astral.sh/uv/). Dependencies and the Python version are declared in `pyproject.toml` / `.python-version` and locked in `uv.lock`.

1. Install uv:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. Install the system packages required by `python-snap7` (the Snap7 shared library).
3. Clone the repository and sync the environment - uv downloads Python 3.12 if needed and creates `.venv` from the lockfile:
   ```bash
   git clone <repo-url>
   cd py-plc-utils
   uv sync
   ```
4. Run any of the readers with `uv run` - they will interactively prompt for connection details (IP addresses, ports, rack/slot values, or OPC UA endpoints). `uv run` syncs the environment automatically, so activating the venv is not required.

### Managing dependencies
```bash
uv add <package>            # add a runtime dependency (updates pyproject.toml and uv.lock)
uv remove <package>         # remove a dependency
uv lock --upgrade           # refresh the lockfile to the latest allowed versions
uv sync                     # align .venv with uv.lock
```

## Usage
- **Siemens S7**
  ```bash
  uv run src/plc_s7_reader.py
  ```
  Choose between direct connection or automatic rack/slot scanning, then read data blocks by specifying offsets, types, and lengths.

- **Modbus TCP**
  ```bash
  uv run src/plc_modbus_reader.py
  ```
  Select coil/discrete/register reads, specify the address range, and optionally parse the returned registers (INT/UINT/REAL/STRING).

- **OPC UA**
  ```bash
  uv run src/plc_opcua_reader.py
  ```
  Connect to an OPC UA endpoint, browse the namespace hierarchically, read node values with their OPC UA data types (Int16, Int32, Double, String, etc.), and export variable snapshots to timestamped text files.

## Development Workflow
- Run `uv run python -m compileall src` before committing to catch syntax errors.
- Commit `uv.lock` together with any `pyproject.toml` change so environments stay reproducible.
- Manual protocol testing is encouraged; include the command you ran and the simulated/real device in your PR notes.
- Refer to `AGENTS.md` for in-depth contributor guidelines on style, commits, and security practices.

## Troubleshooting
- Ensure the required ports (Modbus 502, S7 102, OPC UA 4840 or per server config) are reachable from your network segment.
- When using the OPC UA client, verify certificates or security policies if the server requires them. The client will prompt for the endpoint URL (e.g., `opc.tcp://192.168.1.100:4840`).
- For Siemens S7 access errors, double-check rack/slot values or use the scanner mode to automatically discover valid combinations.

## License
This project has not declared a license. Contact the maintainers before using it in production or distributing modified versions.
