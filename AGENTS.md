AGENTS guide for this repo (Python)

Build/Lint/Test
- Install deps: uv sync
- Run app: uv run python main.py
- Lint: uv run ruff check .
- Format: uv run ruff format .
- Type check: uv run mypy . (optional; add to deps if used)
- Tests: uv run pytest -q
- Single test: uv run pytest -q path/to/test_file.py::TestClass::test_name

Environment and documentation 
- Python 3.13 via uv. Copy .env.default -> .env and set PROJECT_ENDPOINT.
- Azure auth via DefaultAzureCredential (interactive allowed). Run az login if needed.
- Urwid reference: see urwid.md in repo root for examples and API notes.
- Gemini notes: see GEMINI.md for Azure AI Foundry RAG and vector store management with azure-ai-projects.
- Azure Foundry AI: see foundry.md in repo root for examples and API notes.
- Prefer these offline docs rather browser internet

Code Style
- No comments in code. Use clear, self-explanatory, declarative names so comments are unnecessary.
- Imports: stdlib, third-party, local; absolute; separated by blank lines; no unused; alphabetical within groups.
- Formatting: ruff format (PEP 8). Target ~88 cols. Prefer double quotes; preserve existing logging format.
- Types: add type hints to public functions and key internals; explicit return types preferred; avoid typing.Any when possible.
- Naming: snake_case for functions/vars, PascalCase for classes, UPPER_SNAKE_CASE for constants.
- Errors: avoid bare except; catch specific exceptions; log with context; UI actions return (ok: bool, message: str); raise RuntimeError for programmer/flow errors.
- Logging: use logging (no print in library code); store logs under logs/ as in main.py.

Azure AI Foundry (from GEMINI.md)
- SDK: azure-ai-projects + azure-identity; set PROJECT_ENDPOINT (and MODEL_DEPLOYMENT_NAME when creating agents).
- Files: upload via project_client.agents.files.upload_and_poll; associate with vector stores via create_vector_store_and_poll or vector_store_files.create_and_poll; list via agents.files/vector_stores; delete via agents.delete_file/delete_vector_store.
- Agents: create with FileSearchTool bound to vector_store_ids; run via agents.threads/messages/runs APIs.

TUI/Async (Urwid)
- Keep UI non-blocking; schedule work with main_loop.set_alarm_in(0, fn, ...); update via set_text; use lightweight redraw helpers; validate inputs before Azure calls.

Repo Conventions
- Single entry point: main.py; keep business logic small/pure; isolate Azure I/O.
- No Cursor or Copilot rules found (.cursor/ or .github/). If added, mirror rules here with links.
