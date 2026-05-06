# Security Review Design

**Date:** 2026-05-06
**Branch:** fix/security
**Approach:** Automated-first, targeted manual sweep

## Scope

This review covers the full minizen codebase with the goal of identifying and fixing
real security issues, then documenting the security posture in `docs/security.md`.

It does **not** attempt to build a full threat model for a multi-user service — minizen
is a personal CLI tool and the review is proportionate to that threat surface.

## Areas Reviewed

### 1. HTML injection in email template (HIGH)

**File:** `src/minizen/providers/email/template.py`

`_build_more_links` interpolates `a.url` and `a.title` directly from untrusted
Miniflux API data without HTML-escaping. A feed that serves a title containing HTML
(e.g. `<img src=x onerror=...>`) or a `javascript:` URL would land unescaped in the
outgoing email HTML.

`_build_article_cards` similarly interpolates `feed_name` extracted from AI-generated
markdown without escaping — a lower risk (AI output is more controlled) but worth
fixing for defence-in-depth.

**Fix:**
- Apply `html.escape()` to all string values interpolated into HTML attributes or text nodes.
- Filter URLs to `http://` and `https://` schemes only before rendering as `href`.

### 2. `.env` value writing (MEDIUM)

**File:** `src/minizen/cli/commands/setup.py`

The setup wizard writes `.env` values as bare strings. A credential containing a
newline or an unescaped double quote would silently corrupt the file, causing load
failures or — in the newline case — truncating a value and treating the remainder as
a new key.

**Fix:**
- Wrap each value in double quotes and escape embedded backslashes and double quotes
  before writing to `.env`.

### 3. Automated dependency and CI audits (MEDIUM)

**Tools already configured:** `uv audit` (dep CVEs) + `zizmor` (GitHub Actions hardening),
run via `uv run tox -e security`.

**Fix:** Run the tools, review findings, apply any dep upgrades or Actions hardening they
flag.

### 4. Prompt injection (LOW — residual risk, no code fix)

Article content from Miniflux is passed to the AI model verbatim as part of the user
prompt. A crafted article could attempt to override the system prompt or manipulate
the digest output.

For a personal tool where the user controls their own feed subscriptions, the practical
impact is low: an attacker would need to publish a malicious article to a feed the user
subscribes to, and the worst outcome is a distorted digest — not credential theft or
RCE.

**Fix:** No code change. Document as a known residual risk in `docs/security.md`.

### 5. Already-sound areas (no fix needed)

These are verified mitigations — document them in `docs/security.md`:

- **SMTP TLS:** `smtplib.SMTP.starttls()` with no arguments uses
  `ssl.create_default_context()`, which verifies the server certificate against the
  system trust store.
- **Secret storage:** All credentials (API keys, SMTP password) are read from
  environment variables at runtime. The TOML config file contains only non-sensitive
  settings.
- **`.env` file permissions:** The interactive setup wizard writes `.env` with
  `chmod 0o600` (owner read/write only).
- **No credential logging:** Log statements reference only hostnames, ports, and email
  addresses — never keys or passwords.

## Documentation

A new file `docs/security.md` will be created covering:

1. **Threat model** — what minizen protects (credentials in `.env`/env vars, digest
   content integrity) and what it explicitly does not protect against (a compromised
   local machine, a malicious feed subscription with prompt-injection intent).
2. **Mitigations in place** — the five already-sound areas listed above, plus the HTML
   escaping and `.env` quoting fixes added by this work.
3. **Residual risks** — prompt injection (noted, low impact).
4. **Vulnerability reporting** — how to report a security issue.

## Out of scope

- Adding authentication/authorisation to the CLI itself — minizen is a local personal
  tool with no server component; OS-level access control is sufficient.
- Sandboxing the AI model call.
- Validating Miniflux TLS certificates beyond the system trust store.
