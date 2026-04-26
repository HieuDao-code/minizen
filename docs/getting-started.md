# Getting Started with minizen

**minizen** fetches your unread RSS articles from Miniflux, uses Claude AI to curate and summarise the most interesting ones, and emails you a daily digest.

---

## Prerequisites

- A [Miniflux](https://miniflux.app) account (cloud at [reader.miniflux.app](https://reader.miniflux.app) or self-hosted)
- An [Anthropic API key](https://console.anthropic.com)
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

| Prompt                 | Where to find it                                                                                       |
| ---------------------- | ------------------------------------------------------------------------------------------------------ |
| **Miniflux API key**   | Miniflux → Settings → API Keys → Create a new API key                                                  |
| **Anthropic API key**  | [console.anthropic.com](https://console.anthropic.com) → API Keys                                      |
| **SMTP host**          | Your SMTP server hostname (e.g. `smtp.gmail.com`)                                                      |
| **SMTP port**          | SMTP port — use `587` for STARTTLS (works with most providers)                                         |
| **From email address** | The address minizen sends from                                                                         |
| **To email address**   | Where you want to receive digests                                                                      |
| **Email username**     | Your SMTP login username (often your email address)                                                    |
| **Email password**     | Your SMTP password or app password (see your provider's docs)                                          |

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

## Automate with GitHub Actions

minizen ships with a GitHub Actions workflow that runs the digest daily. See `.github/workflows/` in the repository for the workflow file, and add the following secrets to your repository:

- `MINIFLUX_API_KEY`
- `ANTHROPIC_API_KEY`
- `MINIZEN_EMAIL_USERNAME`
- `MINIZEN_EMAIL_PASSWORD`
