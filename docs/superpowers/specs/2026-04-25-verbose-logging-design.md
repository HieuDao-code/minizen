# Verbose Logging Fix — Design Spec

**Date:** 2026-04-25
**Status:** Approved

## Problem

`minizen digest fetch -v` (and `--verbose`) has no effect. Two root causes:

1. **Argument parsing level**: `--verbose/-v` is defined on the root app's callback. In Typer/Click, options on a parent callback must appear before the subcommand group (`minizen --verbose digest fetch`). Placing them after the group (`minizen digest fetch -v`) causes Typer to parse them as unknown options on `fetch`, which rejects them.
2. **`basicConfig` no-op**: `logging.basicConfig()` is silently ignored if the root logger already has handlers, which pydantic-ai and its dependencies (httpx) set up on import.

## Design

### State object

Introduce `src/minizen/cli/state.py` with:

- `State` dataclass — holds `verbose: bool = False`. Designed to be extended with future CLI-level flags (e.g. `--quiet`, `--output-format`).
- `configure_logging(verbose: bool) -> None` — single place for log setup. Uses `logging.basicConfig(force=True)` to override any pre-existing handlers.

### Root callback (`cli/__init__.py`)

- Accepts `ctx: typer.Context` and `verbose: bool`.
- Instantiates `State(verbose=verbose)`, stores it in `ctx.ensure_object(State)`.
- Calls `configure_logging(verbose)`.

### Sub-typer callbacks

Each sub-typer (currently only `digest`) adds its own `@app.callback()` that:

- Accepts `ctx: typer.Context` and `verbose: bool = False`.
- Updates `ctx.obj` (already a `State` instance from the root) with the verbose value.
- Calls `configure_logging(verbose)`.

This is the correct Typer interception point for options placed after a subcommand group name. If the user passes `-v` at the root level (`minizen -v digest fetch`), the root callback handles it. If they pass it at the group level (`minizen digest fetch -v`), the digest callback handles it. Both paths converge on `configure_logging()`.

### `configure_logging`

```python
def configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
        force=True,
    )
```

`force=True` removes any existing handlers and re-applies configuration, making it safe to call even after library imports have already initialised the root logger.

## Files Changed

| File | Change |
|---|---|
| `src/minizen/cli/state.py` | New — `State` dataclass + `configure_logging()` |
| `src/minizen/cli/__init__.py` | Update root callback to use `ctx`, `State`, and `configure_logging()` |
| `src/minizen/cli/commands/digest.py` | Add `@app.callback()` with `--verbose` |
| `tests/cli/test_callback.py` | New — tests for root callback logging behaviour |
| `tests/cli/commands/test_digest.py` | Add verbose callback tests |

## Tests

- `minizen -v run` → root logger level is `DEBUG`
- `minizen digest fetch -v` → root logger level is `DEBUG`
- `minizen run` (no flag) → root logger level is `INFO`
- `minizen digest fetch` (no flag) → root logger level is `INFO`

## Extensibility

Adding a future CLI-level flag (e.g. `--quiet`) requires:
1. Adding the field to `State`.
2. Adding the parameter to the root callback and each sub-typer callback.
3. Using `ctx.obj` to read state in any command that needs it.
