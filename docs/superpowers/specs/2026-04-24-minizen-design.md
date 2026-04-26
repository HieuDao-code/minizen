# minizen — Design Spec

**Date:** 2026-04-24
**Status:** Approved

## Overview

minizen is a personal daily digest tool. It fetches unread RSS articles from Miniflux, uses a pydantic-ai agent to curate and summarise the top N most interesting articles into a cohesive Markdown narrative, converts that to HTML, and emails it to the user. It runs on a daily schedule via GitHub Actions.

---

## Architecture

Layered modules with clean interfaces. Each layer has one job and communicates through typed Pydantic models. Swapping a provider (e.g. replacing Miniflux with another RSS reader) only touches that provider's module.

```
src/minizen/
  cli/
    __init__.py              # Typer app, registers subcommands
    commands/
      run.py                 # minizen run
      setup.py               # minizen setup (interactive wizard)
      config.py              # minizen config show / validate / set
      digest.py              # minizen digest preview / send-test
  config/
    __init__.py
    models.py                # Pydantic settings models
    loader.py                # Loads TOML + resolves secrets from env
  providers/
    rss/
      __init__.py
      miniflux.py            # Miniflux client wrapper
    email/
      __init__.py
      smtp.py                # SMTP sender
  ai/
    __init__.py
    agent.py                 # pydantic-ai agent: curates + summarises articles
  core/
    __init__.py              # package version
    pipeline.py              # fetch → summarise → send orchestration
  main.py                    # entrypoint: calls CLI app
```

---

## Configuration

**Config file** (default `~/.config/minizen/config.toml`, overridable via `--config`):

```toml
[ai]
model = "anthropic:claude-sonnet-4-6"
top_n = 5

[miniflux]
url = "https://my-miniflux.example.com"

[email]
smtp_host = "smtp.gmail.com"
smtp_port = 587
from_addr = "me@example.com"
to_addr = "me@example.com"
```

**Secrets** — stay in environment variables, never in the config file:

| Variable            | Purpose                      |
|---------------------|------------------------------|
| `MINIFLUX_API_KEY`  | Miniflux API authentication  |
| `ANTHROPIC_API_KEY` | Anthropic API (or equivalent for other providers) |
| `EMAIL_USERNAME`    | SMTP login username          |
| `EMAIL_PASSWORD`    | SMTP login password          |

`config/loader.py` loads the TOML and merges env vars into a single validated `Settings` Pydantic model. Locally secrets live in a `.env` file (gitignored); in GitHub Actions they are repository secrets.

---

## CLI Commands

All commands support `--help`. `minizen --help` lists all subcommands (provided by Typer automatically).

| Command | Description |
|---|---|
| `minizen setup` | Interactive wizard: generates `config.toml`, validates all connections |
| `minizen run` | Full pipeline: fetch → summarise → email → mark as read |
| `minizen run --model <model>` | Override AI model for this run |
| `minizen config show` | Print resolved config with secrets redacted |
| `minizen config validate` | Test connections to Miniflux, SMTP, and AI provider |
| `minizen config set <key> <value>` | Persist a config value (e.g. `ai.model`) to `config.toml` |
| `minizen digest preview` | Fetch + summarise, print Markdown to terminal instead of emailing |
| `minizen digest preview --model <model>` | Preview with a specific model |
| `minizen digest send-test` | Send a test email with dummy content to verify SMTP |

`minizen run` is the command invoked by the GitHub Actions schedule. Everything else supports local setup and debugging.

---

## Data Flow

```
minizen run
  │
  ├─ config/loader.py         load config.toml + env secrets → Settings
  │
  ├─ providers/rss/           fetch unread articles from Miniflux → list[Article]
  │   miniflux.py
  │
  ├─ ai/agent.py              pydantic-ai agent receives list[Article]
  │                           picks top N, writes Markdown narrative digest
  │                           returns DigestResult(markdown, articles_used)
  │
  ├─ providers/email/         convert Markdown → HTML (mistune)
  │   smtp.py                 send HTML email via SMTP
  │
  └─ providers/rss/           mark consumed articles as read in Miniflux
      miniflux.py
```

### Key models

```python
class Article(BaseModel):
    id: int
    title: str
    url: str
    content: str
    feed_name: str
    published_at: datetime

class DigestResult(BaseModel):
    markdown: str
    articles_used: list[int]  # article IDs selected by the agent
```

Articles are marked as read **only after** the email sends successfully. If SMTP fails, unread state is preserved and the GitHub Action run is marked as failed.

---

## AI Agent

`ai/agent.py` wraps a pydantic-ai agent. The model is read from `Settings.ai.model` at runtime (e.g. `"anthropic:claude-sonnet-4-6"`, `"openai:gpt-4o"`). Switching providers requires only a config change — the corresponding API key env var must be set.

The agent receives the full list of unread `Article` objects, selects the top `N` most newsworthy, and returns a single cohesive Markdown digest narrative.

The `--model` CLI flag overrides `config.toml` for a single run without persisting the change.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| No unread articles | Exit cleanly, log "No unread articles, nothing to do.", no email sent |
| Connection failure (Miniflux, SMTP, AI provider) | Log clear error message, exit non-zero (GitHub Actions marks run as failed) |
| AI call fails | Log error, exit non-zero, no articles marked as read |
| Email fails | Log error, exit non-zero, no articles marked as read |

Logging uses Python's standard `logging` module. Log level is controlled via `--log-level` (default `INFO`). GitHub Actions captures stdout/stderr in the run log.

Logfire is intentionally excluded — overkill for a personal daily tool. It can be added later; pydantic-ai has native Logfire integration.

---

## Testing

100% coverage target (already configured in `pyproject.toml`). Each layer is tested in isolation.

| Layer | Strategy |
|---|---|
| `config/` | Valid TOML + env vars → correct `Settings`; missing secrets raise clear error |
| `providers/rss/` | Mock Miniflux HTTP client; test `fetch_unread()` returns `list[Article]`; test `mark_as_read()` calls correct API |
| `providers/email/` | Mock `smtplib.SMTP`; test correct headers, recipients, HTML body |
| `ai/` | Mock pydantic-ai agent; test `DigestResult` shape returned correctly; no real LLM calls |
| `core/pipeline.py` | Mock all providers + agent; test call order, early exit on empty articles, no `mark_as_read` on email failure |
| `cli/` | Typer `CliRunner`; test each command's happy path and error output |

---

## GitHub Actions

A scheduled workflow runs `minizen run` daily (e.g. 08:00 UTC). Miniflux API key, Anthropic API key, and email credentials are stored as repository secrets and injected as environment variables at runtime.
