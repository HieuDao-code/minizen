# Configuration Reference

minizen reads its configuration from a TOML file (default `~/.config/minizen/config.toml`)
and secrets from environment variables.

---

## Config file

```toml
[ai]
model = "anthropic:claude-haiku-4-5"
top_n = 5
interests = ["Rust", "AI safety", "climate tech"]  # optional
avoid = ["sports", "celebrity news"]                # optional

[miniflux]
url = "https://reader.miniflux.app"

[email]
smtp_host = "smtp.gmail.com"
smtp_port = 587
from_addr = "you@example.com"
to_addr = "you@example.com"
```

### `[ai]` section

| Key                     | Type           | Default                        | Description |
| ----------------------- | -------------- | ------------------------------ | ----------- |
| `model`                 | string         | `"anthropic:claude-haiku-4-5"` | pydantic-ai model identifier |
| `top_n`                 | integer        | `5`                            | Number of articles selected for full AI summaries; remaining recent articles appear as a "More to read" link list |
| `max_words_per_article` | integer        | `500`                          | Maximum words of article content sent to the LLM per article. Increase for longer summaries, decrease to reduce token usage. |
| `interests`             | list of strings | `[]`                          | Topics for the AI to prioritise when selecting articles (e.g. `["Rust", "AI safety"]`). Omit or leave empty for no preference. |
| `avoid`                 | list of strings | `[]`                          | Topics for the AI to skip when selecting articles (e.g. `["sports", "crypto"]`). Omit or leave empty for no preference. |

#### Interest profile

Use `interests` and `avoid` to guide the AI's article selection without writing any prompts yourself.
Both fields are optional — existing configs without them work unchanged.

```toml
[ai]
model = "anthropic:claude-haiku-4-5"
top_n = 5
interests = ["Rust", "AI safety", "climate tech"]
avoid = ["sports", "celebrity news", "crypto"]
```

The AI will favour articles matching your `interests` and skip those matching `avoid` when choosing the top N.
Both lists accept any freeform topic strings — the more specific, the better.

**During setup** the wizard prompts for both fields interactively:

```
Topics to prioritise (comma-separated, Enter to skip): Rust, AI safety, climate tech
Topics to avoid (comma-separated, Enter to skip): sports, crypto
```

**Non-interactive setup** accepts `--interests` and `--avoid` flags:

```bash
minizen setup --no-interactive \
  --interests "Rust,AI safety,climate tech" \
  --avoid "sports,crypto" \
  --from-addr you@example.com \
  --to-addr you@example.com
```

#### Supported models

minizen uses [pydantic-ai](https://ai.pydantic.dev/) for LLM integration.
Any provider it supports works:

| Provider  | Example `model` value        | Required env var    |
| --------- | ---------------------------- | ------------------- |
| Anthropic | `anthropic:claude-haiku-4-5` | `ANTHROPIC_API_KEY` |
| OpenAI    | `openai:gpt-4o-mini`         | `OPENAI_API_KEY`    |

### `[miniflux]` section

| Key   | Type   | Default                         | Description                                           |
| ----- | ------ | ------------------------------- | ----------------------------------------------------- |
| `url` | string | `"https://reader.miniflux.app"` | Base URL of your Miniflux instance (no `/v1/` suffix) |

### `[email]` section

| Key         | Type    | Default | Description                              |
| ----------- | ------- | ------- | ---------------------------------------- |
| `smtp_host` | string  | —       | SMTP server hostname                     |
| `smtp_port` | integer | —       | SMTP port (typically `587` for STARTTLS) |
| `from_addr` | string  | —       | Sender email address                     |
| `to_addr`   | string  | —       | Recipient email address                  |

---

## Environment variables

Secrets are never stored in the config file. Set them in your shell or in
`~/.config/minizen/.env` (created by `minizen setup` when run interactively).

| Variable                 | Purpose                                         |
| ------------------------ | ----------------------------------------------- |
| `MINIFLUX_API_KEY`       | Miniflux API key for authentication             |
| `ANTHROPIC_API_KEY`      | Anthropic API key (if using an Anthropic model) |
| `OPENAI_API_KEY`         | OpenAI API key (if using an OpenAI model)       |
| `MINIZEN_EMAIL_USERNAME` | SMTP login username                             |
| `MINIZEN_EMAIL_PASSWORD` | SMTP login password or app password             |

---

## Custom config path

The default config path is `~/.config/minizen/config.toml`.
Pass a custom path with `--config`:

```bash
minizen run --config /path/to/config.toml
```

---

## Manual setup (without `minizen setup`)

You can configure minizen entirely by hand — no wizard required.

### 1. Create the config file

Copy this template to `~/.config/minizen/config.toml` and fill in your values:

```toml
[miniflux]
url = "https://reader.miniflux.app"  # or your self-hosted URL

[email]
smtp_host = "smtp.gmail.com"
smtp_port = 587
from_addr = "you@example.com"
to_addr = "you@example.com"

[ai]
model = "anthropic:claude-haiku-4-5"
top_n = 5
# max_words_per_article = 500                        # default: 500
# interests = ["Rust", "AI safety", "climate tech"]  # optional
# avoid = ["sports", "celebrity news", "crypto"]      # optional
```

Use `minizen config set` to update individual values later:

```bash
minizen config set ai.top_n 10
minizen config set ai.model "openai:gpt-4o-mini"
```

### 2. Set secrets via `.env` file

Create `~/.config/minizen/.env` (same directory as `config.toml`):

```dotenv
MINIFLUX_API_KEY=your-miniflux-api-key
ANTHROPIC_API_KEY=your-anthropic-key   # or OPENAI_API_KEY
MINIZEN_EMAIL_USERNAME=your-smtp-username
MINIZEN_EMAIL_PASSWORD=your-smtp-app-password
```

Restrict permissions so only your user can read it:

```bash
chmod 600 ~/.config/minizen/.env
```

### 3. Set secrets via shell rc file

As an alternative to `.env`, export the variables in your shell profile
(`~/.bashrc`, `~/.zshrc`, or equivalent):

```bash
export MINIFLUX_API_KEY="your-miniflux-api-key"
export ANTHROPIC_API_KEY="your-anthropic-key"   # or OPENAI_API_KEY
export MINIZEN_EMAIL_USERNAME="your-smtp-username"
export MINIZEN_EMAIL_PASSWORD="your-smtp-app-password"
```

Reload your shell after editing: `source ~/.zshrc` (or `source ~/.bashrc`).

### 4. Verify the setup

```bash
minizen config validate
```

A clean output confirms minizen can read all required values.
