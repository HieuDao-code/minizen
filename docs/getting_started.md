# Getting Started with minizen

**minizen** fetches your unread RSS articles from Miniflux, uses AI to curate and summarise the most interesting ones, and emails you a daily digest.

---

## Prerequisites

- A [Miniflux](https://miniflux.app) account (cloud at [reader.miniflux.app](https://reader.miniflux.app) or self-hosted)
- An AI provider API key (see [Configuration reference](configuration.md) for supported providers)
- An SMTP-capable email account (Gmail is the most common — see below)

---

## Installation

```bash
pip install minizen
```

Or with `uv`:

```bash
uv tool install minizen
```

---

## Setup

Run the interactive wizard:

```bash
minizen setup
```

You will be prompted for:

| Prompt                     | Where to find it                                                             |
| -------------------------- | ---------------------------------------------------------------------------- |
| **AI model**               | Model identifier as `provider:model`, e.g. `anthropic:claude-haiku-4-5`, `openai:gpt-4o` or `deepseek:deepseek-chat` |
| **Number of top articles** | How many articles to include in the digest (default: 5)                      |
| **SMTP host**              | Your SMTP server hostname (e.g. `smtp.gmail.com`)                            |
| **SMTP port**              | SMTP port — use `587` for STARTTLS (works with most providers)               |
| **From email address**     | The address minizen sends from                                               |
| **To email address**       | Where you want to receive digests                                            |
| **Email username**         | Your SMTP login username (often your email address)                          |
| **Email password**         | Your SMTP password or app password (see your provider's docs)                |
| **Miniflux API key**       | Miniflux → Settings → API Keys → Create a new API key                        |
| **AI provider API key**    | The wizard prompts for whichever provider your model names, and writes the matching variable — `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`, and so on |

### Email provider setup

minizen works with any SMTP server that supports STARTTLS on port 587.

**Gmail** is the most common choice. To use it:

1. Go to your Google Account → Security
2. Under "How you sign in to Google", enable 2-Step Verification if not already on
3. Search for "App passwords" in your Google Account settings
4. Create a new App Password (e.g. name it `minizen`)
5. Copy the 16-character password — use this as your **Email password**

For other providers (Fastmail, Outlook, Proton Mail Bridge, etc.), consult your
provider's SMTP documentation. The `smtp_host`, `smtp_port`, username, and password
fields map directly to your provider's settings.

See the [Configuration reference](configuration.md) for all available settings.

The wizard writes two files:

- `~/.config/minizen/config.toml` — non-secret settings (SMTP host/port, addresses, AI model)
- `~/.config/minizen/.env` — secrets (API keys, email password)

---

## Verify your setup

```bash
minizen config validate
```

---

## Test it

Fetch your unread articles (no AI, no email):

```bash
minizen digest fetch
```

Preview the AI-generated digest in your terminal (no email sent):

```bash
minizen digest preview
```

Send a test digest email without marking articles as read:

```bash
minizen digest send-test
```

---

## Run the full pipeline

```bash
minizen run
```

This fetches unread articles, generates the digest, emails it, and marks the articles as read in Miniflux.

---

## Run without a config file

You can pass all credentials directly as flags — useful in CI/CD where you do not
want to store credentials on disk:

```bash
minizen run \
  --miniflux-api-key  "$MINIFLUX_API_KEY" \
  --from-addr         "digest@example.com" \
  --to-addr           "me@example.com" \
  --smtp-host         "smtp.gmail.com" \
  --smtp-port         587 \
  --email-username    "$EMAIL_USER" \
  --email-password    "$EMAIL_PASS"
```

Flags override the corresponding values in the config file when both are present.
