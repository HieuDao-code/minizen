# Robustness — Structured Error Handling

**Date:** 2026-05-06  
**Branch:** feat/robust  
**Status:** Approved

## Goal

Replace raw tracebacks with clear, actionable error messages when the Miniflux API, AI model, or SMTP server fails. The tool should fail fast with a one-liner on stderr and exit code 1.

## Exception Hierarchy

A new module `src/minizen/exceptions.py` defines:

```python
class MinizenError(Exception): ...     # base — caught by CLI
class MinifluxError(MinizenError): ... # Miniflux API / network failures
class AIError(MinizenError): ...       # pydantic-ai / model failures
class EmailError(MinizenError): ...    # SMTP delivery failures
```

Each subclass carries only a human-readable message string. No extra fields.

## Provider-Level Error Handling

Each provider wraps its own known exceptions:

| Provider | Caught exceptions | Raised as |
|---|---|---|
| `MinifluxProvider.fetch_recent()` | `miniflux.ClientError`, `miniflux.ServerError`, `OSError` | `MinifluxError("Miniflux API error: {detail}")` |
| `DigestAgent.run()` | `pydantic_ai.ModelHTTPError`, `pydantic_ai.UnexpectedModelBehavior`, `pydantic_ai.UsageLimitExceeded` | `AIError("AI model error: {detail}")` |
| `EmailProvider.send()` | `smtplib.SMTPException`, `OSError` | `EmailError("Email delivery failed: {detail}")` |

The pipeline (`run_pipeline`) is unchanged — errors bubble up naturally without additional catching.

## CLI Integration

A single top-level handler in `main.py` catches all `MinizenError` subclasses:

```python
except MinizenError as e:
    typer.echo(f"Error: {e}", err=True)
    raise typer.Exit(code=1)
```

This prints a clean one-liner to stderr with exit code 1. No traceback is shown to the user. Existing `--verbose` / logging behaviour is unaffected.

## Testing

Unit tests using `pytest-mock` for each failure point:

- **`MinifluxProvider`** — mock `miniflux.Client.get_entries` raising `ClientError` and `OSError`; assert `MinifluxError` with correct message
- **`DigestAgent`** — mock `Agent.run_sync` raising pydantic-ai exceptions; assert `AIError`
- **`EmailProvider`** — mock `smtplib.SMTP` raising `SMTPException`; assert `EmailError`
- **CLI** — mock `run_pipeline` raising each subclass; assert stderr output and exit code 1
