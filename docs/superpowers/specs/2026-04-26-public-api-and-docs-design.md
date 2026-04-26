# Public API & Documentation — Design Spec

**Date:** 2026-04-26
**Status:** Approved

## Overview

Two parallel improvements:

1. **Public API** — expose minizen's core building blocks so users can embed the tool in their own Python scripts via `from minizen import ...`.
2. **Documentation** — expand and restructure the docs site with a proper homepage, architecture diagram, configuration reference, FAQ, and AI disclaimer.

---

## Part 1: Public API

### Goal

Allow users to write scripts like:

```python
from minizen import load_settings, run_pipeline, Settings
from minizen.config import AIConfig, EmailConfig, MinifluxConfig
from minizen.providers.rss import Article, MinifluxProvider
from minizen.providers.email import EmailProvider
from minizen.ai import DigestAgent, DigestResult
from minizen.core import run_pipeline
```

Both flat imports (`from minizen import X`) and deep imports (`from minizen.config import X`) must work.

### Approach

Sub-package exposure: each sub-package's `__init__.py` declares its own public symbols; the top-level `__init__.py` re-exports all of them and defines `__all__`.

### Exported symbols per package

| Package | Public symbols |
|---|---|
| `minizen.config` | `Settings`, `AIConfig`, `EmailConfig`, `MinifluxConfig`, `load_settings` |
| `minizen.providers.rss` | `Article`, `MinifluxProvider` |
| `minizen.providers.email` | `EmailProvider` |
| `minizen.ai` | `DigestAgent`, `DigestResult` |
| `minizen.core` | `run_pipeline` |
| `minizen` (top-level) | All of the above |

### What stays internal

- `render_email` / `template.py` — implementation detail of the pipeline, not user-facing.
- `cli/` — CLI commands are not part of the library API.
- `config/loader.py` internals — only `load_settings` is exposed, not the individual loaders.

### Changes required

1. `src/minizen/config/__init__.py` — export `Settings`, `AIConfig`, `EmailConfig`, `MinifluxConfig`, `load_settings`
2. `src/minizen/providers/rss/__init__.py` — export `Article`, `MinifluxProvider`
3. `src/minizen/providers/email/__init__.py` — export `EmailProvider`
4. `src/minizen/ai/__init__.py` — export `DigestAgent`, `DigestResult`
5. `src/minizen/core/__init__.py` — export `run_pipeline`
6. `src/minizen/__init__.py` — re-export all of the above, define `__all__`, keep `__version__`

---

## Part 2: Documentation

### Approach

New dedicated pages per topic, registered in `zensical.toml`. Existing pages are updated in place where content needs expanding.

### Nav structure (final)

```
Home → Getting Started → How It Works → Configuration → FAQ → AI Disclaimer → Changelog
```

### Page changes

#### `README.md` (rendered as `docs/index.md`)

Expand from 2 lines to a real homepage:

- One-line tagline
- What it does (3–4 bullet features)
- Quick-start snippet (install + run)
- Links to Getting Started and How It Works

#### `docs/how_it_works.md`

- Add a Mermaid diagram showing the pipeline: Miniflux → DigestAgent → Email → mark-as-read
- Expand the written explanation to cover each step and the tech behind it (miniflux, pydantic-ai, SMTP)

#### `docs/getting-started.md`

- Make email setup provider-agnostic: describe SMTP generically, with Gmail as the worked example
- Reference `configuration.md` for the full env var list rather than duplicating it

#### `docs/configuration.md` (new)

- All TOML config keys with types and defaults
- Supported LLM providers (Anthropic, OpenAI) and the `model` identifier format
- Required environment variables table: variable name, purpose, where to get it

#### `docs/faq.md` (new)

Common questions and troubleshooting:

- What RSS readers are supported?
- Which LLM providers work?
- Can I use a non-Gmail SMTP server?
- What happens if there are no unread articles?
- How do I test without sending a real email?
- The digest didn't arrive — what do I check?

#### `docs/ai-disclaimer.md` (new)

- Discloses that minizen uses AI to generate digest content (pydantic-ai + Claude/OpenAI)
- Discloses that the tool itself was developed with the assistance of AI (Claude Code)

### `zensical.toml` nav update

Add three new entries after "How It Works" and before "Changelog":

```toml
[[project.nav]]
Configuration = "configuration.md"

[[project.nav]]
FAQ = "faq.md"

[[project.nav]]
"AI Disclaimer" = "ai-disclaimer.md"
```

---

## Out of scope

- Develop section (packages + links)
- Third-party import documentation page
- Programmatic doc generation (e.g. mkdocstrings)
