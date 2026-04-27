# Documentation Improvements Design

**Date:** 2026-04-27
**Branch:** feat/improve

---

## Overview

Three documentation todos from `docs/todo.md`:

1. Add module and function docstrings throughout the codebase
2. Document manual credential setup (rc file and env vars)
3. Consolidate duplicate default constants into a single place

---

## 1. Module Docstrings

Most core files already have complete Google-style docstrings. What's missing are module-level docstrings.

### Files requiring module docstrings

| File | Docstring |
|---|---|
| `src/minizen/main.py` | `"""Entry point for the minizen CLI application."""` |
| `src/minizen/cli/__init__.py` | `"""CLI application root — registers all sub-commands."""` |
| `src/minizen/cli/state.py` | `"""Shared CLI state and logging configuration."""` |
| `src/minizen/cli/commands/__init__.py` | `"""CLI command modules for the minizen application."""` |
| `src/minizen/cli/commands/config.py` | `"""CLI commands to inspect and update the minizen configuration."""` |
| `src/minizen/cli/commands/digest.py` | `"""CLI commands to preview or test the digest without sending."""` |
| `src/minizen/cli/commands/run.py` | `"""CLI command to run the full fetch-summarise-email pipeline."""` |
| `src/minizen/cli/commands/setup.py` | `"""Interactive and non-interactive setup wizard for minizen."""` |
| `src/minizen/config/__init__.py` | `"""Configuration loading and model definitions for minizen."""` |
| `src/minizen/core/__init__.py` | `"""Core pipeline logic for the minizen digest workflow."""` |
| `src/minizen/ai/__init__.py` | `"""AI agent for curating and summarising RSS articles."""` |
| `src/minizen/providers/email/__init__.py` | `"""Email delivery provider for minizen."""` |
| `src/minizen/providers/rss/__init__.py` | `"""RSS feed provider for fetching articles from Miniflux."""` |

No changes to existing function/class docstrings — they already follow Google-style conventions.

---

## 2. Defaults Consolidation

### Problem

The following constants are duplicated across multiple files:

| Constant | Value | Duplicated in |
|---|---|---|
| Config path | `~/.config/minizen/config.toml` | `config.py`, `digest.py`, `run.py` |
| Miniflux URL | `"https://reader.miniflux.app"` | `models.py`, `loader.py`, `setup.py` |
| AI model | `"anthropic:claude-haiku-4-5"` | `models.py`, `run.py`, `setup.py`, `config.py` (inline) |
| Top N | `5` | `models.py`, `run.py`, `setup.py`, `config.py` (inline) |
| SMTP host | `"smtp.gmail.com"` | `setup.py` (two places) |
| SMTP port | `587` | `setup.py` (two places) |

### Solution

Create `src/minizen/config/defaults.py`:

```python
"""Default values for all minizen configuration settings."""

from pathlib import Path

DEFAULT_CONFIG_PATH: Path = Path.home() / ".config" / "minizen" / "config.toml"
DEFAULT_MINIFLUX_URL: str = "https://reader.miniflux.app"
DEFAULT_MODEL: str = "anthropic:claude-haiku-4-5"
DEFAULT_TOP_N: int = 5
DEFAULT_SMTP_HOST: str = "smtp.gmail.com"
DEFAULT_SMTP_PORT: int = 587
```

### Changes per file

- **`config/models.py`** — import and use `DEFAULT_MINIFLUX_URL`, `DEFAULT_MODEL`, `DEFAULT_TOP_N` as Pydantic field defaults
- **`config/loader.py`** — replace hardcoded fallback URL with `DEFAULT_MINIFLUX_URL`
- **`config/__init__.py`** — re-export `defaults` module or constants as needed
- **`cli/commands/config.py`** — replace `_DEFAULT_CONFIG` with `DEFAULT_CONFIG_PATH`; replace inline `'anthropic:claude-haiku-4-5'` and `5` in `show()` with imports
- **`cli/commands/digest.py`** — replace `_DEFAULT_CONFIG` with `DEFAULT_CONFIG_PATH`
- **`cli/commands/run.py`** — replace `_DEFAULT_CONFIG`, `_DEFAULT_MODEL`, `_DEFAULT_TOP_N` with imports; remove `_DEFAULT_MINIFLUX_URL` (already covered)
- **`cli/commands/setup.py`** — replace `_DEFAULT_CONFIG`, `_DEFAULT_MODEL`, `_DEFAULT_TOP_N` with imports; replace hardcoded smtp defaults and miniflux URL with imports

---

## 3. Manual Credential Setup Docs

### Problem

`docs/configuration.md` already documents the TOML structure and env var table but does not explain how to set up credentials manually without running `minizen setup`.

### Solution

Add a **"Manual setup"** section to `docs/configuration.md` covering:

1. **Create config.toml by hand** — copy the reference TOML block, point to `minizen config set` for edits
2. **Create `.env` file manually** — show the file format, recommend `chmod 600`
3. **Shell rc file approach** — show `export` statements to add to `~/.bashrc` / `~/.zshrc`

No new file needed.

---

## Testing

No new tests required — this change is purely documentation and constant extraction. Existing test suite covers all affected code paths. After the change, run:

```bash
uv run pytest
uv run ruff check && uv run ruff format --check
uv run ty check
```
