# Security Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix HTML injection and `.env` value-quoting vulnerabilities, run automated security tools and fix findings, and document the security posture in `docs/security.md`.

**Architecture:** Three targeted code fixes (HTML escaping in the email template, `.env` value quoting in the setup wizard, automated tool findings) plus a new documentation file. No new modules — all changes are additions to existing files.

**Tech Stack:** Python stdlib `html` module for escaping, `uv audit` + `zizmor` for automated checks, Markdown for `docs/security.md`.

---

## File Map

| File | Change |
|------|--------|
| `src/minizen/providers/email/template.py` | Add `html.escape()` to `_build_more_links` and `_build_article_cards`; filter non-`http(s)` URLs |
| `src/minizen/cli/commands/setup.py` | Add `_quote_env_value` helper; apply it when writing `.env` in `_setup_interactive` |
| `tests/providers/email/test_template.py` | Add tests for HTML injection defence |
| `tests/cli/commands/test_setup.py` | Update `.env` content assertions to expect quoted values; add special-char test |
| `docs/security.md` | New file documenting threat model, mitigations, residual risks |

---

## Task 1: Fix HTML injection in the email template

**Files:**
- Modify: `src/minizen/providers/email/template.py:39-70, 73-86`
- Test: `tests/providers/email/test_template.py`

### Background

`_build_more_links` (line 85) interpolates `a.url` and `a.title` from untrusted
Miniflux API data directly into HTML without escaping. `_build_article_cards`
(line 64) interpolates `feed_name` from AI-processed HTML without escaping.

A feed that sets its title to `<img src=x onerror=alert(1)>` or its URL to
`javascript:alert(1)` would land unescaped in the outgoing email.

The fix is:
- `html.escape()` on every string value interpolated into HTML text nodes or attributes.
- Filter URLs to `http://` / `https://` schemes in `_build_more_links`.

- [ ] **Step 1: Write failing tests for HTML escaping and URL filtering**

Add to `tests/providers/email/test_template.py`. The existing imports (`from datetime import UTC, datetime`, `from minizen.providers.rss.miniflux import Article`, `from minizen.providers.email.template import render_email`) are already present — only add the test functions:

```python
def test_render_email_escapes_article_title_in_more_links() -> None:
    # arrange
    extra = Article(
        id=1,
        title='<script>alert("xss")</script>',
        url="https://example.com/article",
        content="content",
        feed_name="Feed",
        published_at=datetime(2026, 5, 6, tzinfo=UTC),
    )

    # act
    html, _ = render_email(markdown="Hello", extra_articles=[extra])

    # assert
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_render_email_escapes_article_url_in_more_links() -> None:
    # arrange
    extra = Article(
        id=2,
        title="Normal Title",
        url='https://example.com/path?q=<"injected">',
        content="content",
        feed_name="Feed",
        published_at=datetime(2026, 5, 6, tzinfo=UTC),
    )

    # act
    html, _ = render_email(markdown="Hello", extra_articles=[extra])

    # assert
    assert '<"injected">' not in html
    assert "&lt;" in html


def test_render_email_filters_javascript_url_in_more_links() -> None:
    # arrange
    extra = Article(
        id=3,
        title="Malicious",
        url="javascript:alert(1)",
        content="content",
        feed_name="Feed",
        published_at=datetime(2026, 5, 6, tzinfo=UTC),
    )

    # act
    html, _ = render_email(markdown="Hello", extra_articles=[extra])

    # assert
    assert "More to read" not in html


def test_render_email_escapes_feed_name_in_article_cards() -> None:
    # arrange
    markdown = (
        "Intro.\n\n"
        "**<script>evil</script>**\n\n"
        "## [Title](https://example.com)\n\n"
        "Summary.\n"
    )

    # act
    html, _ = render_email(markdown=markdown)

    # assert
    assert "<script>evil</script>" not in html
    assert "&lt;script&gt;" in html
```

- [ ] **Step 2: Run the new tests to confirm they fail**

```bash
uv run pytest tests/providers/email/test_template.py::test_render_email_escapes_article_title_in_more_links tests/providers/email/test_template.py::test_render_email_escapes_article_url_in_more_links tests/providers/email/test_template.py::test_render_email_filters_javascript_url_in_more_links tests/providers/email/test_template.py::test_render_email_escapes_feed_name_in_article_cards -v
```

Expected: 4 FAIL (unescaped values are present / javascript URL is not filtered).

- [ ] **Step 3: Apply the fix in `template.py`**

At the top of the file, add the import on line 4 (after `import math`):

```python
from html import escape
```

Replace the body of `_build_more_links` (lines 83-86):

```python
    if not articles:
        return ""
    items = "".join(
        f'<li><a href="{escape(a.url)}">{escape(a.title)}</a></li>'
        for a in articles
        if a.url.startswith(("https://", "http://"))
    )
    return f'<div class="more-links"><h3>More to read</h3><ul>{items}</ul></div>'
```

Replace the feed_name interpolation in `_build_article_cards` (lines 63-67):

```python
        result += (
            f'<div class="article-card">'
            f'<span class="feed-badge">{escape(feed_name)}</span>'
            f"{content}"
            f"</div>"
        )
```

- [ ] **Step 4: Run all template tests to verify they pass**

```bash
uv run pytest tests/providers/email/test_template.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/minizen/providers/email/template.py tests/providers/email/test_template.py
git commit -m "fix: escape HTML and filter URLs in email template"
```

---

## Task 2: Fix `.env` value quoting in the setup wizard

**Files:**
- Modify: `src/minizen/cli/commands/setup.py:135-145`
- Test: `tests/cli/commands/test_setup.py`

### Background

`_setup_interactive` writes credential values to `.env` as bare strings (line 135-140).
A password containing a newline silently corrupts the file; one containing `"` can
break dotenv parsers that handle quoting. The fix is to quote every value using
double-quote wrapping with backslash-escaping of `\` and `"`.

`python-dotenv` (used in `config/loader.py`) handles quoted values transparently —
`MINIFLUX_API_KEY="my-key"` is parsed as `my-key`.

The non-interactive path (`_setup_non_interactive`) reads secrets from existing env
vars and does not write `.env`, so it is unaffected.

- [ ] **Step 1: Update existing `.env` content assertions in `test_setup.py`**

The existing `test_setup_writes_env_file` (line 98-117) and
`test_setup_writes_openai_key_for_openai_model` (line 259-286) check for bare values.
After the fix they must expect quoted values.

Replace lines 113-117:

```python
    assert 'MINIFLUX_API_KEY="miniflux-api-key"' in content
    assert 'ANTHROPIC_API_KEY="anthropic-api-key"' in content
    assert 'MINIZEN_EMAIL_USERNAME="email-user"' in content
    assert 'MINIZEN_EMAIL_PASSWORD="email-password"' in content
```

Replace line 285:

```python
    assert 'OPENAI_API_KEY="openai-api-key"' in content
```

- [ ] **Step 2: Add a failing test for special-character passwords**

Add to `tests/cli/commands/test_setup.py`:

```python
def test_setup_quotes_env_values_with_special_chars(tmp_path: Path) -> None:
    # arrange
    config_path = tmp_path / "config.toml"
    runner = CliRunner()

    # act
    runner.invoke(
        app,
        ["setup", "--config", str(config_path)],
        input=(
            "\n"  # model (default)
            "\n"  # top_n (default)
            "\n"  # smtp host (default)
            "\n"  # smtp port (default)
            "from@example.com\n"
            "to@example.com\n"
            "email-user\n"
            'p@ss"word\n'
            "miniflux-api-key\n"
            "anthropic-api-key\n"
        ),
    )

    # assert
    env_path = tmp_path / ".env"
    content = env_path.read_text()
    assert r'MINIZEN_EMAIL_PASSWORD="p@ss\"word"' in content
```

- [ ] **Step 3: Run updated and new tests to confirm they fail**

```bash
uv run pytest tests/cli/commands/test_setup.py::test_setup_writes_env_file tests/cli/commands/test_setup.py::test_setup_writes_openai_key_for_openai_model tests/cli/commands/test_setup.py::test_setup_quotes_env_values_with_special_chars -v
```

Expected: 3 FAIL (bare values present, quoted value not present).

- [ ] **Step 4: Add `_quote_env_value` and apply it in `_setup_interactive`**

Add after the `_write_config` function definition (before `_setup_interactive`) in
`src/minizen/cli/commands/setup.py`:

```python
def _quote_env_value(value: str) -> str:
    """Wrap a .env value in double quotes, escaping backslashes and double quotes.

    Args:
        value: The raw credential string to quote.

    Returns:
        The value wrapped in double quotes with ``\\`` and ``"`` escaped,
        safe for writing to a ``.env`` file parsed by python-dotenv.
    """
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
```

In `_setup_interactive`, replace the `.env` write block (lines 135-140):

```python
    env_path.write_text(
        f"MINIFLUX_API_KEY={_quote_env_value(miniflux_api_key)}\n"
        f"{key_env_var}={_quote_env_value(ai_api_key)}\n"
        f"MINIZEN_EMAIL_USERNAME={_quote_env_value(email_username)}\n"
        f"MINIZEN_EMAIL_PASSWORD={_quote_env_value(email_password)}\n"
    )
```

- [ ] **Step 5: Run all setup tests to verify they pass**

```bash
uv run pytest tests/cli/commands/test_setup.py -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/minizen/cli/commands/setup.py tests/cli/commands/test_setup.py
git commit -m "fix: quote credential values written to .env"
```

---

## Task 3: Run automated security tools and fix any findings

**Files:** Varies — depends on findings.

- [ ] **Step 1: Run `uv audit`**

```bash
uv run tox -e security
```

`uv audit` checks all locked dependencies against the OSV advisory database.
`zizmor` checks `.github/workflows/*.yml` for GitHub Actions hardening issues.

- [ ] **Step 2: Fix `uv audit` findings (if any)**

For each advisory:
- If a safe upgrade exists: `uv add <package>@<safe-version>` and commit.
- If no fix is available: note it as accepted risk in `docs/security.md`.

- [ ] **Step 3: Fix `zizmor` findings (if any)**

Common `zizmor` findings and fixes:
- `unpinned-uses`: pin each `uses: owner/action@vN` to a full SHA, e.g.
  `uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683`
- `excessive-permissions`: scope permissions blocks to the minimum needed.
- `pull-request-target`: avoid `pull_request_target` with untrusted code.

After applying fixes, re-run:

```bash
uv run tox -e security
```

Expected: no findings from either tool.

- [ ] **Step 4: Commit (if any changes were made)**

```bash
git add .github/workflows/ uv.lock pyproject.toml
git commit -m "fix: address automated security tool findings"
```

---

## Task 4: Write `docs/security.md`

**Files:**
- Create: `docs/security.md`

- [ ] **Step 1: Write the file**

```markdown
# Security

## Threat Model

minizen is a personal CLI tool that runs locally. It holds credentials for three
external services (Miniflux, an SMTP server, and an AI provider). The assets worth
protecting are those credentials and the integrity of the digest output.

minizen does **not** protect against:
- A compromised local machine (an attacker with shell access can read `.env` directly).
- A feed author who publishes malicious article content aimed at manipulating the
  AI digest output (see Residual Risks below).

## Mitigations

### Credential storage

All secrets (API keys, SMTP credentials) are read at runtime from environment
variables. The TOML config file contains only non-sensitive settings (SMTP host/port,
email addresses, AI model name) and carries no access credentials.

The interactive setup wizard writes credentials to a `.env` file with permissions
`0o600` (owner read/write only). Each value is double-quote-wrapped and
backslash-escaped so that special characters cannot corrupt the file format.

### SMTP transport security

Outbound email uses `smtplib.SMTP.starttls()` with no custom SSL context, which
defaults to `ssl.create_default_context()`. This verifies the SMTP server's
certificate against the system trust store and negotiates TLS 1.2 or higher.

### Email content safety

Article titles and URLs sourced from the Miniflux API are HTML-escaped using
`html.escape()` before being interpolated into the email template. URLs are
additionally filtered to `http://` and `https://` schemes to prevent
`javascript:` injection.

Feed names extracted from AI-generated Markdown are also HTML-escaped before
rendering.

### No credential logging

Log statements record only hostnames, ports, and email addresses. API keys and
passwords are never passed to the logging subsystem.

### Dependency and CI auditing

Dependencies are checked against the OSV advisory database via `uv audit` on every
CI run. GitHub Actions workflow files are audited with `zizmor`. Both are also
available locally via `uv run tox -e security`.

## Residual Risks

### Prompt injection

Article content fetched from Miniflux is passed verbatim to the AI model as part of
the user prompt. A feed author could craft article text intended to override the
system prompt or manipulate the digest output (e.g., inserting fabricated articles).

For a personal tool where the user controls their own feed subscriptions, practical
impact is low: exploitation requires publishing a malicious article to a feed the
user already subscribes to, and the worst outcome is a distorted digest — not
credential theft or code execution. No mitigation is applied; the risk is accepted.

## Reporting a Vulnerability

To report a security issue, open a [GitHub issue](https://github.com/hieudao-code/minizen/issues)
with the label `security`. For sensitive disclosures, email the maintainer directly
before opening a public issue.
```

- [ ] **Step 2: Verify the file renders correctly**

```bash
cat docs/security.md
```

Expected: readable Markdown with all sections present.

- [ ] **Step 3: Commit**

```bash
git add docs/security.md
git commit -m "docs: add security.md with threat model and mitigations"
```

---

## Task 5: Full test suite and coverage check

- [ ] **Step 1: Run the full test suite**

```bash
uv run pytest
```

Expected: all tests PASS, coverage at 100%.

- [ ] **Step 2: Run the security tools one final time**

```bash
uv run tox -e security
```

Expected: no findings from `uv audit` or `zizmor`.
