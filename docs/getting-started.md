# Getting Started with minizen

**minizen** fetches your unread RSS articles from Miniflux, uses Claude AI to curate and summarise the most interesting ones, and emails you a daily digest.

---

## Prerequisites

- A [Miniflux](https://miniflux.app) account (cloud at [reader.miniflux.app](https://reader.miniflux.app) or self-hosted)
- An [Anthropic API key](https://console.anthropic.com)
- A Gmail account with an [App Password](https://support.google.com/accounts/answer/185833)

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
| **SMTP host**          | Default: `smtp.gmail.com`                                                                              |
| **SMTP port**          | Default: `587`                                                                                         |
| **From email address** | The Gmail address minizen sends from                                                                   |
| **To email address**   | Where you want to receive digests                                                                      |
| **Email username**     | Your Gmail address                                                                                     |
| **Email password**     | Your Gmail [App Password](https://support.google.com/accounts/answer/185833) (not your login password) |

### Getting a Gmail App Password

1. Go to your Google Account → Security
2. Under "How you sign in to Google", enable 2-Step Verification if not already on
3. Search for "App passwords" in your Google Account settings
4. Create a new App Password (e.g. name it `minizen` and press "Create")
5. Copy the 16-character password — use this as your **Email password**

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
