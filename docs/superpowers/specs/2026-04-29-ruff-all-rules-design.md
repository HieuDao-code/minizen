# Ruff All-Rules Cleanup Design

**Date:** 2026-04-29
**Branch:** feat/all-ruff

## Overview

`select = ["ALL"]` is already enabled in `pyproject.toml`. This spec covers how to handle every
violation surfaced by that change: which rules to ignore (and where), and which to fix in code.

## Rule Ignores

### `**/tests/**`

Add `"D"` to the existing per-file ignore block for tests:

```toml
"**/tests/**" = [
    "D",  # pydocstyle
    # existing ignores ...
]
```

Test function names are the documentation; adding docstrings adds noise without value.

### `src/minizen/cli/**`

Add a new per-file ignore block:

```toml
"src/minizen/cli/**" = [
    "FBT002",  # boolean-default-value-positional-argument — Typer requires bool defaults
]
```

Typer introspects `bool` default values to wire up CLI flags. Using keyword-only or non-bool
alternatives would break the Typer API contract.

## Code Fixes

### `builtin-open` (PTH123) — fix everywhere

Replace all `open(path, ...)` calls with `path.open(...)`:

| File | Count |
|---|---|
| `src/minizen/cli/commands/config.py` | 2 |
| `src/minizen/config/loader.py` | 1 |
| `src/minizen/providers/email/template.py` | 1 |
| `tests/cli/commands/test_config.py` | 1 |
| `tests/cli/commands/test_setup.py` | 1 |

### `call-date-today` (DTZ011) — use UTC

Replace `date.today()` with `datetime.now(tz=UTC).date()` in all three locations:

- `src/minizen/cli/commands/digest.py`
- `src/minizen/core/pipeline.py`
- `src/minizen/providers/email/template.py`

Using UTC avoids DST ambiguity and makes the code testable with `freeze_time` from freezegun,
which patches `datetime.datetime.now()` but not `date.today()`.

### `unused-lambda-argument` (ARG005) — use `_` convention

In two test files, replace `lambda *a, **k: None` with `lambda *_, **__: None`:

- `tests/cli/commands/test_config.py`
- `tests/config/test_loader.py`

### `import-outside-top-level` (PLC0415) — move imports to top

In `tests/cli/commands/test_config.py`, three `import tomllib` statements are placed inside test
function bodies in the assert block. Move the single import to the top of the file.

### `unused-function-argument` (ARG001) — remove unused fixture

In `tests/cli/commands/test_run.py:274`, the `mocker: MockerFixture` parameter is unused. Remove it.
