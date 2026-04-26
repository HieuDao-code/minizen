# Configuration Reference

minizen reads its configuration from a TOML file (default `~/.config/minizen/config.toml`)
and secrets from environment variables.

---

## Config file

```toml
[ai]
model = "anthropic:claude-haiku-4-5"
top_n = 5

[miniflux]
url = "https://reader.miniflux.app"

[email]
smtp_host = "smtp.gmail.com"
smtp_port = 587
from_addr = "you@example.com"
to_addr = "you@example.com"
```

### `[ai]` section

| Key | Type | Default | Description |
|---|---|---|---|
| `model` | string | `"anthropic:claude-haiku-4-5"` | pydantic-ai model identifier |
| `top_n` | integer | `5` | Maximum articles to include in the digest |

#### Supported models

minizen uses [pydantic-ai](https://ai.pydantic.dev/) for LLM integration.
Any provider it supports works:

| Provider | Example `model` value | Required env var |
|---|---|---|
| Anthropic | `anthropic:claude-haiku-4-5` | `ANTHROPIC_API_KEY` |
| OpenAI | `openai:gpt-4o-mini` | `OPENAI_API_KEY` |

### `[miniflux]` section

| Key | Type | Default | Description |
|---|---|---|---|
| `url` | string | `"https://reader.miniflux.app"` | Base URL of your Miniflux instance (no `/v1/` suffix) |

### `[email]` section

| Key | Type | Default | Description |
|---|---|---|---|
| `smtp_host` | string | — | SMTP server hostname |
| `smtp_port` | integer | — | SMTP port (typically `587` for STARTTLS) |
| `from_addr` | string | — | Sender email address |
| `to_addr` | string | — | Recipient email address |

---

## Environment variables

Secrets are never stored in the config file. Set them in your shell or in
`~/.config/minizen/.env` (created by `minizen setup` when run interactively).

| Variable | Purpose |
|---|---|
| `MINIFLUX_API_KEY` | Miniflux API key for authentication |
| `ANTHROPIC_API_KEY` | Anthropic API key (if using an Anthropic model) |
| `OPENAI_API_KEY` | OpenAI API key (if using an OpenAI model) |
| `MINIZEN_EMAIL_USERNAME` | SMTP login username |
| `MINIZEN_EMAIL_PASSWORD` | SMTP login password or app password |

---

## Custom config path

The default config path is `~/.config/minizen/config.toml`.
Pass a custom path with `--config`:

```bash
minizen run --config /path/to/config.toml
```
