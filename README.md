# py-plc-utils

Interactive command-line tools for reading data from industrial PLCs over **Siemens S7**, **Modbus TCP**, and **OPC UA**.

Each tool is a self-contained, interactive Python script built for quick diagnostics and manual data collection in the field: point it at a device, answer a few prompts, and read values back. There is no configuration file and no daemon — everything is entered at the prompt.

> **Read-only by design.** These tools only *read* from devices. None of them write values back to a PLC.

## Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Siemens S7](#siemens-s7)
  - [Modbus TCP](#modbus-tcp)
  - [OPC UA](#opc-ua)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Requirements

- **Python 3.12+** (declared in `.python-version`; uv installs it for you if missing)
- Network access to the target device on the relevant port — S7 `102`, Modbus `502`, OPC UA `4840` by default
- [uv](https://docs.astral.sh/uv/) for dependency management

No system libraries are required. The S7 tool uses `python-snap7` 3.x, which is a pure-Python implementation over raw sockets — the old Snap7 C shared library is **not** needed.

## Installation

```bash
git clone git@github.com:sforna/py-plc-utils.git
cd py-plc-utils
uv sync
```

`uv sync` creates `.venv` from `uv.lock`, downloading Python 3.12 if needed. Run the tools with `uv run`, which syncs the environment automatically — activating the virtualenv is not necessary.

### Managing dependencies

```bash
uv add <package>      # add a dependency (updates pyproject.toml and uv.lock)
uv remove <package>   # remove a dependency
uv lock --upgrade     # refresh the lockfile to the latest allowed versions
uv sync               # align .venv with uv.lock
```

## Usage

### Siemens S7

```bash
uv run src/plc_s7_reader.py
```

Reads data blocks and memory areas from Siemens S7 PLCs. On start you choose a connection mode:

1. **Direct connection** — you supply IP, port (default `102`), rack (default `0`) and slot (default `0`).
2. **Scan mode** — you supply only the IP, and the tool sweeps every rack (`0`–`7`) and slot (`0`–`10`) combination, 88 in total, probing each by reading one byte from a test DB. Useful when the rack/slot of a device is unknown. Connection timeouts during the sweep are normal and are suppressed.

Scan mode reports two categories: PLCs where the test DB was readable, and PLCs that accepted the connection but refused the DB read. If none of the former are found, you can still connect to the latter.

Once connected, you pick a memory area and read from it in a loop:

| Option | Area | Notes |
| --- | --- | --- |
| 1 | `DB` | Data Block — prompts for a DB number (default `200`) |
| 2 | `PE` | Process inputs |
| 3 | `PA` | Process outputs |
| 4 | `MK` | Merker / flag memory |
| 5 | `CT` | Counters |
| 6 | `TM` | Timers |

Then supply a start offset and a data type:

| Type | Size read | Extra prompt |
| --- | --- | --- |
| `bool` | 1 byte | Bit position `0`–`7` |
| `bool_array` | `ceil(n / 8)` bytes | Number of elements; prints each element indexed |
| `int` | 2 bytes | — |
| `udint` | 4 bytes | — |
| `real` | 4 bytes | — |
| `string` | *n* + 2 bytes | S7 string capacity (`1`–`254` bytes, excluding the header) |
| `char` | *n* bytes | Positive byte count for a CHAR array, without a header |

For `string`, the start offset must point to the S7 STRING header: the first byte stores the maximum capacity, the second stores the current text length. The reader decodes only that many text bytes using `python-snap7`'s default Latin-1 encoding. For example, at DB201 offset 686, `FE 05 32 31 2F 31 30 ...` represents `21/10`; enter capacity `254` to read 256 bytes including the header.

For `char`, the start offset points directly to the first character. Enter the number of bytes to read (for example, `20` for `ARRAY[0..19] OF CHAR`). All requested bytes are decoded as Latin-1, preserving spaces and NUL characters. This type has no 254-byte STRING limit.

### Modbus TCP

```bash
uv run src/plc_modbus_reader.py
```

Prompts for IP, port (default `502`) and Unit/Slave ID (default `1`), then loops over reads. Choose a register type:

| Option | Register type | Returns |
| --- | --- | --- |
| 1 | Coils (`0x`) | Bits |
| 2 | Discrete Inputs (`1x`) | Bits |
| 3 | Holding Registers (`4x`) | 16-bit words |
| 4 | Input Registers (`3x`) | 16-bit words |

Bit reads ask for a start address and a bit count, and print the raw values. Register reads additionally parse the result into a data type, with the register count derived automatically:

| Type | Registers read |
| --- | --- |
| `int16`, `uint16` | 1 |
| `int32`, `uint32`, `dword`, `float32` | 2 |
| `string` | `ceil(chars / 2)` |

For the 32-bit types you are asked for the **register order** (`big` or `little`, default `big`), since devices differ in how they split a 32-bit value across two 16-bit registers. If a value looks like nonsense, try the other order.

### OPC UA

```bash
uv run src/plc_opcua_reader.py
```

Accepts either a bare IP (`192.168.1.100`, expanded to `opc.tcp://192.168.1.100:4840`) or a full endpoint URL (`opc.tcp://host:port`). The main menu offers:

**1. Read the value of a node** — enter a Node ID and get the value plus its OPC UA data type. Accepted forms:

```
ns=2;i=1001          namespace 2, integer identifier
ns=1;s=Temperature   namespace 1, string identifier
i=85                 Objects folder (default namespace)
```

**2. Browse nodes** — interactive hierarchical navigation starting at the Objects folder. Children are listed with their node class, and variables show their current value and OPC UA type inline. Enter a number to descend into an object or inspect a variable, `0` to go back one level, `00` to return to the main menu. When inspecting a variable you can re-read its value live.

**3. Export variables to a file** — dumps the **direct child** variables of a given node to a timestamped text file in the current directory, named `variables_<node>_<YYYYmmdd_HHMMSS>.txt`, with each entry showing name, Node ID, OPC UA type and value. The default is `i=85` (the Objects folder); since the export only covers direct children and the Objects folder usually contains folders rather than variables, you will normally want to pass the Node ID of a specific folder.

Vendor-specific structures show up as children of the Objects folder — for example, Siemens servers expose interfaces created in TIA Portal under a `ServerInterfaces` folder. Use **Browse nodes** to discover the Node IDs you need, then feed them to the read or export options.

## Development

- Run `uv run python -m compileall src` before committing to catch syntax errors.
- Commit `uv.lock` alongside any `pyproject.toml` change so environments stay reproducible.
- Run `uv run python -m unittest discover -s tests` for S7 STRING and CHAR tests, including mocked CLI reads. These tests do not require a PLC.
- Test hardware interactions against a real or simulated device and note in your PR which one you used and the command you ran.

## Troubleshooting

**Connection refused or timeouts** — confirm the port is reachable from your network segment (S7 `102`, Modbus `502`, OPC UA `4840` or whatever the server is configured for). A firewall between you and the plant network is the usual culprit.

**S7: connection succeeds but reads fail** — the rack/slot is likely wrong, or the DB is not accessible. Use scan mode to discover valid rack/slot combinations. Note that on S7-1200/1500 you must also disable "optimized block access" on any DB you intend to read this way.

**Modbus: values look wrong** — check the register order for 32-bit types, and remember that some devices document addresses with a 1-based offset relative to what the protocol actually sends.

**OPC UA: connection rejected** — the server may require a security policy or a trusted client certificate. This client connects anonymously with no security policy, which some servers refuse by default.

## License

This project is released under the [MIT License](LICENSE).

It depends on third-party packages under their own licenses:

| Package | License |
| --- | --- |
| [python-snap7](https://github.com/gijzelaerr/python-snap7) | MIT |
| [pymodbus](https://github.com/pymodbus-dev/pymodbus) | BSD-3-Clause |
| [asyncua](https://github.com/FreeOpcUa/opcua-asyncio) | LGPL-3.0-or-later |

`asyncua` is copyleft (LGPL), unlike the others. The LGPL is designed to allow use from differently-licensed programs, and this project only imports it as an ordinary dependency installed separately by uv — it does not bundle, vendor, or modify it. Distributing this source under MIT is therefore consistent with that. If you ever ship a frozen binary that *embeds* `asyncua` (PyInstaller, Nuitka and similar), the LGPL's relinking obligations come into play and you should check the terms. This summary is informational, not legal advice.
