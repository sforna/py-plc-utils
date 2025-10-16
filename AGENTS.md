# Repository Guidelines
Contributors help maintain reliable PLC utilities for Modbus, Siemens S7, and OPC UA devices. Use this guide to keep changes focused, tested, and secure.

## Project Structure & Module Organization
- `src/` hosts the interactive readers (`plc_modbus_reader.py`, `plc_s7_reader.py`, `plc_opcua_reader.py`) that encapsulate protocol-specific logic and user prompts.
- `requirements.txt` pins runtime dependencies; update it in lockstep with code that imports new libraries.
- `venv/` is a local virtual environment; recreate it rather than committing its contents.
- Store connection secrets (PLC IPs, credentials, UA endpoints) in a `.env` file loaded via `python-dotenv`. Exclude `.env` from commits.

## Build, Test, and Development Commands
- `python -m venv venv && source venv/bin/activate` creates and activates a clean workspace.
- `pip install -r requirements.txt` installs PLC client libraries (python-snap7, pymodbus, asyncua).
- `python src/plc_modbus_reader.py` or `python src/plc_s7_reader.py` runs the interactive readers for manual testing.
- `python -m compileall src` quickly checks for syntax errors before opening a PR.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indents, descriptive snake_case for functions, and ALL_CAPS for connection constants.
- Keep modules single-purpose; add helpers near the readers they support and factor reusable utilities into new files within `src/`.
- When handling PLC data, document endianness, register width, and expected units inline to prevent misinterpretation.

## Testing Guidelines
- Adopt `pytest` for new automated coverage; place tests in a `tests/` package mirroring the module layout.
- Name tests `test_<feature>_<condition>` for traceability.
- Use `pytest -q` locally; when hardware access is required, isolate those tests with markers so they can be skipped in CI.

## Commit & Pull Request Guidelines
- The history uses short, imperative messages (e.g., `remove useless code`); keep summaries under ~70 characters and expand rationale in the body when needed.
- Reference related issues, list affected PLC protocols, and include manual test notes (command run, device used) in the PR description.
- Attach screenshots or logs only when they clarify protocol interactions; redact any sensitive endpoint details.

## Security & Configuration Tips
- Never commit live PLC credentials or raw trace captures.
- Review `.env` and sample config files before pushing to ensure they contain only mock data or documented placeholders.
