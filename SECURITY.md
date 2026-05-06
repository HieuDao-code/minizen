# Security Considerations

This document describes the security model of minizen, the mitigations in place,
and known limitations to be aware of when deploying or contributing to the project.

---

## Credential Management

### How secrets are stored

minizen never stores secrets in the TOML configuration file.  All sensitive values
are kept in a separate `.env` file and read at runtime via environment variables:

| Secret | Environment variable |
|--------|---------------------|
| Miniflux API key | `MINIFLUX_API_KEY` |
| SMTP password | `MINIZEN_EMAIL_PASSWORD` |
| SMTP username | `MINIZEN_EMAIL_USERNAME` |
| AI provider API key | `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` |

The `minizen setup` wizard writes this file with mode `0600` (owner-read/write only)
and restricts the config directory to mode `0700`.  The TOML config file is also
written with mode `0600`.

### SecretStr in memory

`MinifluxConfig.api_key` and `EmailConfig.password` are typed as Pydantic
`SecretStr`.  This prevents the values from appearing in `repr()` output, log
messages, or tracebacks that stringify the settings objects.  The raw string is
only unwrapped via `.get_secret_value()` immediately before it is passed to a
third-party call (the Miniflux client or `smtplib.SMTP.login`).

### `.env` file format

Values written to the `.env` file are wrapped in double quotes and have embedded
`\` and `"` characters escaped.  This prevents a password that contains a newline
from injecting additional key=value pairs into the file (environment variable
injection).

### Secrets via CLI flags

`minizen run` accepts `--email-password`, `--miniflux-api-key`, and other
secret-bearing flags for convenience.  **Avoid using these on shared machines**:
command-line arguments are visible to other users via `/proc/<pid>/cmdline` and
`ps aux`, and may be recorded in shell history.  Prefer the `.env` file or
environment variables instead.

---

## Transport Security

### SMTP

All SMTP connections use STARTTLS (`smtplib.SMTP.starttls()`) before sending
credentials.  Plain-text SMTP on port 25 is not supported.  Python's default SSL
context is used, which enforces certificate verification against the system CA
bundle.

### Miniflux API

Connections to the Miniflux instance use the URL configured by the user.  The
official `miniflux` Python client handles TLS for `https://` URLs.  Using a
plain `http://` Miniflux URL will transmit the API key in the clear; always
configure a TLS-terminated URL.

### AI provider API

API keys for Anthropic/OpenAI are passed to the respective provider SDKs
(via pydantic-ai).  Both providers enforce TLS on their endpoints.

---

## HTML Email Safety

The Jinja-free email template in `providers/email/template.py` embeds
untrusted data from two sources:

1. **RSS article metadata** (`Article.url`, `Article.title`) — data originating
   from external RSS feeds.
2. **AI-generated Markdown** — produced by the configured LLM from the article
   content.

### Mitigations in place

* `Article.title` is passed through `html.escape()` before insertion into the
  `<a>` text node in the "More to read" section.
* `Article.url` is validated with `_safe_url()`, which accepts only `http` and
  `https` schemes and falls back to `"#"` for anything else (e.g. `javascript:`
  URIs).  The accepted URL is then `html.escape()`-d before use in the `href`
  attribute.
* The main digest body is produced by **mistune**, which escapes HTML characters
  in Markdown source by default, limiting the attack surface from AI-generated
  content.

### Residual risk

Email clients vary widely in how they render HTML.  JavaScript execution is
generally disabled in mail clients, but HTML injection could still affect
layout or embed tracking pixels.  If the Miniflux instance ingests feeds from
untrusted sources, review article content before it reaches the LLM.

---

## Authentication & Authorisation

minizen is a **personal CLI tool** with no server component and no multi-user
access model.  Access controls are therefore at the operating system level:

* The config directory (`~/.config/minizen/` by default) is restricted to `0700`.
* The config TOML and `.env` files are restricted to `0600`.
* Anyone with read access to those files, or to the process environment, can
  obtain the stored credentials.

There is no built-in role-based access control, session management, or rate
limiting.  If the tool is deployed in a shared or multi-tenant environment,
use OS-level isolation (separate user accounts, containers, etc.).

---

## Configuration Integrity

The `minizen config set` command enforces an allowlist (`_ALLOWED_KEYS`) that
restricts which TOML keys can be updated via the CLI.  Secret values
(`api_key`, `password`) are not in the allowlist and can only be set through
environment variables or the `setup` wizard.

---

## Dependency Security

Project dependencies are audited with [zizmor](https://github.com/woodruffw/zizmor)
(included as a dev dependency).  Run `uv run zizmor` to check for known
vulnerabilities in the dependency tree.

Keep dependencies up to date.  The `pyproject.toml` pins lower bounds for all
direct dependencies; run `uv lock --upgrade` periodically to pull in security
patches.

---

## Reporting a Vulnerability

Please open a private security advisory on the GitHub repository rather than
filing a public issue.  Include a description of the vulnerability, steps to
reproduce, and the potential impact.
