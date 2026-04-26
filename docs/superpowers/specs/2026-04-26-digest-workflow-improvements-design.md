# Digest Workflow Improvements

## Goal

Fix the setup wizard bugs, add OpenAI support, harden `.env` permissions, and make
`minizen run` usable without a local config file by accepting all settings as CLI flags.

---

## 1. Bug Fixes

### `_write_config` — missing miniflux section

`_write_config` currently writes only `[email]` and `[ai]` sections. It must also write
a `[miniflux]` section with the default URL so `load_settings` can read it back.

```toml
[miniflux]
url = "https://reader.miniflux.app"
```

### `load_settings` — crash on missing miniflux section

`load_settings` does `raw["miniflux"]["url"]` which raises `KeyError` for existing
configs that predate this fix. Change to:

```python
miniflux_raw = raw.get("miniflux", {})
url = miniflux_raw.get("url", "https://reader.miniflux.app")
```

---

## 2. Setup Wizard

### Prompt order (interactive)

New order — API keys move to the end:

1. AI model (default: `anthropic:claude-haiku-4-5`)
2. SMTP host, SMTP port
3. From email address, to email address
4. Email username, email password
5. Miniflux API key
6. AI provider API key (label derived from model prefix — see below)

### OpenAI support

The required AI API key is derived from the model prefix:

| Model prefix | Env var written to `.env` | Prompt label |
|---|---|---|
| `anthropic:` | `ANTHROPIC_API_KEY` | `Anthropic API key` |
| `openai:` | `OPENAI_API_KEY` | `OpenAI API key` |

Any other prefix produces an error: `Unknown model provider: <prefix>`. This applies
to both interactive and non-interactive modes.

**Non-interactive**: instead of always requiring `ANTHROPIC_API_KEY`, derive the
required env var from `--model` (defaulting to `anthropic:claude-haiku-4-5`).

### `.env` permissions

After writing `.env`, set permissions to `0o600`:

```python
env_path.chmod(0o600)
```

---

## 3. `minizen run` — flag-based override (Option A)

### New flags

All flags are optional (`None` by default). They map 1-to-1 to `Settings` fields:

| Flag | Settings field |
|---|---|
| `--miniflux-url` | `settings.miniflux.url` |
| `--miniflux-api-key` | `settings.miniflux.api_key` |
| `--model` | `settings.ai.model` |
| `--top-n` | `settings.ai.top_n` |
| `--from-addr` | `settings.email.from_addr` |
| `--to-addr` | `settings.email.to_addr` |
| `--smtp-host` | `settings.email.smtp_host` |
| `--smtp-port` | `settings.email.smtp_port` |
| `--email-username` | `settings.email.username` |
| `--email-password` | `settings.email.password` |

### Merge logic

A new `apply_overrides(settings, **flags) -> Settings` helper in `run.py` returns a
new `Settings` with any non-`None` flag value replacing the corresponding field. It
uses `settings.model_copy(update={...})` (Pydantic v2).

### Config file not found

When `FileNotFoundError` is raised:

1. Attempt to build a bare `Settings` from flags alone (using model field defaults
   where applicable).
2. If any required field is still absent, print a clear error listing the missing
   flags and exit with code 1.
3. If all fields are covered, continue without a config file.

`apply_overrides` is then called with the same flags to apply any non-`None` values
(redundant but keeps the code path uniform).

---

## 4. Testing

- **`tests/cli/test_setup.py`**: parametrised tests for interactive and non-interactive
  modes covering anthropic and openai model prefixes, prompt order, `.env` content,
  `.env` permissions (`stat().st_mode`), and the unknown-prefix error.
- **`tests/config/test_loader.py`**: test `load_settings` with a TOML that has no
  `[miniflux]` section — assert URL defaults to `https://reader.miniflux.app`.
- **`tests/cli/test_run.py`**: test `apply_overrides` directly, test `run` with no
  config file but all flags provided, and test flag override of a loaded setting.

---

## 5. Documentation

Update `docs/getting_started.md` and any other docs that reference `ANTHROPIC_API_KEY`
to mention `OPENAI_API_KEY` as an alternative. Add a section on running without a
config file using flags.

---

## What This Does Not Cover

- Support for model providers other than `anthropic:` and `openai:`
- Encrypting `.env` at rest beyond filesystem permissions
- Migrating existing `.env` files to 600 permissions automatically
