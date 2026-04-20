# Copilot Instructions — Argus_Overview

Start by reading `CLAUDE.md` and keep changes aligned with its constraints.

## Project Focus
- Python desktop app for EVE multiboxing.
- UI stack: PySide6.
- Platform abstraction is required: Linux and Windows implementations should stay in their platform modules.

## Guardrails
- Keep business logic out of UI widgets where possible.
- Do not hardcode user-specific paths or machine assumptions.
- Never commit secrets, tokens, or local environment artifacts.

## Preferred Commands
- `python -m pip install -e ".[dev,linux]"`
- `ruff check .`
- `ruff format .`
- `pytest -q`

## Validation Expectations
- Run lint + tests before proposing final changes.
- If touching platform-specific code, verify no regressions on the other platform layer.
