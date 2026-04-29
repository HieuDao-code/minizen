# Ruff All-Rules Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve every violation introduced by `select = ["ALL"]` in ruff, using per-file ignores where the framework forces the pattern, and code fixes everywhere else.

**Architecture:** Four categories of change — config ignores (pyproject.toml), `Path.open()` migration (PTH123), UTC datetime migration (DTZ011), and test hygiene fixes (ARG005, PLC0415, ARG001). DTZ011 fixes unlock proper `freeze_time` usage in tests.

**Tech Stack:** Python 3.14, ruff 0.15.x, pytest, freezegun

---

## Files Modified

| File | What changes |
|---|---|
| `pyproject.toml` | Add `"D"` + `"FBT002"` per-file ignores |
| `src/minizen/cli/commands/config.py` | 2× `open()` → `Path.open()` |
| `src/minizen/config/loader.py` | 1× `open()` → `Path.open()` |
| `src/minizen/cli/commands/digest.py` | `date.today()` → `datetime.now(tz=UTC).date()`; update import |
| `src/minizen/core/pipeline.py` | same datetime fix |
| `src/minizen/providers/email/template.py` | same datetime fix |
| `tests/cli/commands/test_config.py` | move `import tomllib` to top; 3× `open()` → `Path.open()`; `lambda *a, **k` → `lambda *_, **__` |
| `tests/cli/commands/test_setup.py` | 4× `open()` → `Path.open()` |
| `tests/cli/commands/test_digest.py` | use `freeze_time` + hardcoded date string in subject assertion; update import |
| `tests/config/test_loader.py` | `lambda *a, **k` → `lambda *_, **__` |
| `tests/cli/commands/test_run.py` | remove unused `mocker: MockerFixture` from one test |
| `tests/core/test_pipeline.py` | use `freeze_time` + hardcoded date in 2 subject assertions; update import |

---

### Task 1: Add per-file ignores to pyproject.toml

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add `"D"` to the tests block and a new CLI block**

  In `pyproject.toml`, the current `[tool.ruff.lint.per-file-ignores]` block is:

  ```toml
  [tool.ruff.lint.per-file-ignores]
  "**/tests/**" = [
    "PLR2004", # magic-value-comparison
    "PLR0913", # too-many-arguments
    "S101",    # assert
    "S105",    # hardcoded-password-string
    "S106",    # hardcoded-password-func-arg
  ]
  "src/minizen/cli/commands/setup.py" = ["PLR0913"]
  "src/minizen/cli/commands/run.py" = ["PLR0913"]
  "src/minizen/providers/email/template.py" = ["E501"]
  ```

  Replace with:

  ```toml
  [tool.ruff.lint.per-file-ignores]
  "**/tests/**" = [
    "D",       # pydocstyle
    "PLR2004", # magic-value-comparison
    "PLR0913", # too-many-arguments
    "S101",    # assert
    "S105",    # hardcoded-password-string
    "S106",    # hardcoded-password-func-arg
  ]
  "src/minizen/cli/**" = [
    "FBT002",  # boolean-default-value-positional-argument — Typer requires bool defaults
  ]
  "src/minizen/cli/commands/setup.py" = ["PLR0913"]
  "src/minizen/cli/commands/run.py" = ["PLR0913"]
  "src/minizen/providers/email/template.py" = ["E501"]
  ```

- [ ] **Step 2: Verify FBT002 and D violations are gone**

  Run: `uv run ruff check 2>&1 | grep -E "^(FBT002|D1)"`

  Expected: no output (zero matches)

- [ ] **Step 3: Commit**

  ```bash
  git add pyproject.toml
  git commit -m "chore(ruff): add per-file ignores for pydocstyle and FBT002"
  ```

---

### Task 2: Fix `builtin-open` in source files (PTH123)

**Files:**
- Modify: `src/minizen/cli/commands/config.py:26,88`
- Modify: `src/minizen/config/loader.py:36`

- [ ] **Step 1: Fix `config.py` — two occurrences**

  In `src/minizen/cli/commands/config.py`:

  Line 26 (inside `show`):
  ```python
  # before
  with open(config, "rb") as f:
  # after
  with config.open("rb") as f:
  ```

  Line 88 (inside `set_value`):
  ```python
  # before
  with open(config, "rb") as f:
  # after
  with config.open("rb") as f:
  ```

  The `config` parameter is already typed as `Path`, so no import change needed.

- [ ] **Step 2: Fix `loader.py` — one occurrence**

  In `src/minizen/config/loader.py`, line 36:
  ```python
  # before
  with open(config_path, "rb") as f:
  # after
  with config_path.open("rb") as f:
  ```

  `config_path` is typed as `Path` — no import change needed.

- [ ] **Step 3: Verify PTH123 is gone from source files**

  Run: `uv run ruff check src/ 2>&1 | grep PTH123`

  Expected: no output

- [ ] **Step 4: Run tests**

  Run: `uv run pytest -x -q`

  Expected: all tests pass

- [ ] **Step 5: Commit**

  ```bash
  git add src/minizen/cli/commands/config.py src/minizen/config/loader.py
  git commit -m "fix(ruff): replace builtin open() with Path.open() in source files"
  ```

---

### Task 3: Fix `call-date-today` in source files (DTZ011)

**Files:**
- Modify: `src/minizen/cli/commands/digest.py`
- Modify: `src/minizen/core/pipeline.py`
- Modify: `src/minizen/providers/email/template.py`

- [ ] **Step 1: Fix `digest.py`**

  Change the import at the top of `src/minizen/cli/commands/digest.py`:
  ```python
  # before
  from datetime import date
  # after
  from datetime import UTC, datetime
  ```

  Change the `date.today()` call in `send_test` (around line 131):
  ```python
  # before
  today = date.today().strftime("%B %-d, %Y")
  # after
  today = datetime.now(tz=UTC).date().strftime("%B %-d, %Y")
  ```

- [ ] **Step 2: Fix `pipeline.py`**

  Change the import at the top of `src/minizen/core/pipeline.py`:
  ```python
  # before
  from datetime import date
  # after
  from datetime import UTC, datetime
  ```

  Change the `date.today()` call (around line 46):
  ```python
  # before
  today = date.today().strftime("%B %-d, %Y")
  # after
  today = datetime.now(tz=UTC).date().strftime("%B %-d, %Y")
  ```

- [ ] **Step 3: Fix `template.py`**

  Change the import at the top of `src/minizen/providers/email/template.py`:
  ```python
  # before
  from datetime import date
  # after
  from datetime import UTC, datetime
  ```

  Change the `date.today()` call in `render_email` (around line 80):
  ```python
  # before
  today = date.today().strftime("%B %-d, %Y")
  # after
  today = datetime.now(tz=UTC).date().strftime("%B %-d, %Y")
  ```

- [ ] **Step 4: Verify DTZ011 is gone from source files**

  Run: `uv run ruff check src/ 2>&1 | grep DTZ011`

  Expected: no output

- [ ] **Step 5: Run tests**

  Run: `uv run pytest -x -q`

  Expected: all tests pass

- [ ] **Step 6: Commit**

  ```bash
  git add src/minizen/cli/commands/digest.py src/minizen/core/pipeline.py src/minizen/providers/email/template.py
  git commit -m "fix(ruff): replace date.today() with datetime.now(tz=UTC).date()"
  ```

---

### Task 4: Update date assertions in tests to use `freeze_time`

The tests in `test_digest.py` and `test_pipeline.py` assert the email subject using
`date.today()`. Now that source uses `datetime.now(tz=UTC).date()`, we pin the date
with `freeze_time` so assertions are deterministic.

**Files:**
- Modify: `tests/cli/commands/test_digest.py`
- Modify: `tests/core/test_pipeline.py`

- [ ] **Step 1: Update `test_digest.py`**

  The function `test_digest_send_test_sends_email` currently uses:
  ```python
  from datetime import date
  ...
  today = date.today().strftime("%B %-d, %Y")
  mock_email.send.assert_called_once_with(
      subject=f"[TEST] Your Daily Zen — {today}",
      ...
  )
  ```

  Replace `from datetime import date` at the top with:
  ```python
  from freezegun import freeze_time
  ```

  Then decorate the test and use a hardcoded date string:
  ```python
  @freeze_time("2026-04-29")
  def test_digest_send_test_sends_email(mocker: MockerFixture) -> None:
      # arrange
      mock_settings = _make_settings_mock()
      mocker.patch(
          "minizen.cli.commands.digest.load_settings", return_value=mock_settings
      )
      mock_articles = [MagicMock()]
      mock_rss = MagicMock()
      mock_rss.fetch_unread.return_value = mock_articles
      mocker.patch("minizen.cli.commands.digest.MinifluxProvider", return_value=mock_rss)
      mock_result = MagicMock()
      mock_result.markdown = "## Digest"
      mock_agent = MagicMock()
      mock_agent.run.return_value = mock_result
      mocker.patch("minizen.cli.commands.digest.DigestAgent", return_value=mock_agent)
      mock_email = MagicMock()
      mocker.patch("minizen.cli.commands.digest.EmailProvider", return_value=mock_email)
      mocker.patch(
          "minizen.cli.commands.digest.render_email",
          return_value=("<h2>Digest</h2>", "## Digest"),
      )
      runner = CliRunner()

      # act
      result = runner.invoke(app, ["digest", "send-test"])

      # assert
      assert result.exit_code == 0
      mock_email.send.assert_called_once_with(
          subject="[TEST] Your Daily Zen — April 29, 2026",
          html="<h2>Digest</h2>",
          plain_text="## Digest",
      )
      mock_rss.mark_as_read.assert_not_called()
  ```

- [ ] **Step 2: Update `test_pipeline.py` — `test_pipeline_runs_full_flow`**

  Change the import at the top of `tests/core/test_pipeline.py`:
  ```python
  # before
  from datetime import UTC, date, datetime
  # after
  from datetime import UTC, datetime

  from freezegun import freeze_time
  ```

  Decorate `test_pipeline_runs_full_flow` and replace the dynamic `today` computation:
  ```python
  @freeze_time("2026-04-29")
  def test_pipeline_runs_full_flow(mocker: MockerFixture) -> None:
      # arrange
      articles = [_make_article(1), _make_article(2)]
      mock_rss = MagicMock()
      mock_rss.fetch_unread.return_value = articles
      mock_email = MagicMock()
      mock_digest_result = MagicMock()
      mock_digest_result.markdown = "## Digest"
      mock_digest_result.articles_used = [1, 2]
      mock_agent = MagicMock()
      mock_agent.run.return_value = mock_digest_result
      mocker.patch("minizen.core.pipeline.MinifluxProvider", return_value=mock_rss)
      mocker.patch("minizen.core.pipeline.EmailProvider", return_value=mock_email)
      mocker.patch("minizen.core.pipeline.DigestAgent", return_value=mock_agent)
      mocker.patch(
          "minizen.core.pipeline.render_email",
          return_value=("<h2>Digest</h2>", "## Digest"),
      )
      settings = _make_settings()

      # act
      run_pipeline(settings=settings)

      # assert
      mock_rss.fetch_unread.assert_called_once_with()
      mock_agent.run.assert_called_once_with(articles=articles)
      mock_email.send.assert_called_once_with(
          subject="Your Daily Zen — April 29, 2026",
          html="<h2>Digest</h2>",
          plain_text="## Digest",
      )
      mock_rss.mark_as_read.assert_called_once_with(article_ids=[1, 2])
  ```

- [ ] **Step 3: Update `test_pipeline.py` — `test_pipeline_sends_email_with_fixture_data`**

  Decorate with `@freeze_time("2026-04-29")` and replace:
  ```python
  # before
  today = date.today().strftime("%B %-d, %Y")
  ...
  mock_email.send.assert_called_once_with(
      subject=f"Your Daily Zen — {today}",
      ...
  )

  # after (remove the today line, use hardcoded string)
  mock_email.send.assert_called_once_with(
      subject="Your Daily Zen — April 29, 2026",
      html=sent_html,
      plain_text=digest_markdown,
  )
  ```

  The full updated test:
  ```python
  @freeze_time("2026-04-29")
  def test_pipeline_sends_email_with_fixture_data(mocker: MockerFixture) -> None:
      # arrange
      fixtures = Path(__file__).parents[1] / "fixtures"
      raw = json.loads((fixtures / "miniflux_response.json").read_text())
      digest_markdown = (fixtures / "digest_result.md").read_text()

      articles = [
          Article(
              id=entry["id"],
              title=entry["title"],
              url=entry["url"],
              content=entry["content"],
              feed_name=entry["feed"]["title"],
              published_at=datetime.fromisoformat(entry["published_at"]),
          )
          for entry in raw["entries"]
      ]
      article_ids = [a.id for a in articles]

      mock_rss = MagicMock()
      mock_rss.fetch_unread.return_value = articles
      mock_agent = MagicMock()
      mock_agent.run.return_value = MagicMock(
          markdown=digest_markdown,
          articles_used=article_ids,
      )
      mock_email = MagicMock()

      mocker.patch("minizen.core.pipeline.MinifluxProvider", return_value=mock_rss)
      mocker.patch("minizen.core.pipeline.DigestAgent", return_value=mock_agent)
      mocker.patch("minizen.core.pipeline.EmailProvider", return_value=mock_email)
      mocker.patch(
          "minizen.core.pipeline.render_email",
          wraps=email_template.render_email,
      )
      settings = _make_settings()

      # act
      run_pipeline(settings=settings)

      # assert
      sent_html = mock_email.send.call_args.kwargs["html"]
      mock_email.send.assert_called_once_with(
          subject="Your Daily Zen — April 29, 2026",
          html=sent_html,
          plain_text=digest_markdown,
      )
      assert all(kw in sent_html for kw in ["Rust", "LLM", "Apple", "Platforms", "Webb"])
      mock_rss.mark_as_read.assert_called_once_with(article_ids=article_ids)
  ```

- [ ] **Step 4: Run tests**

  Run: `uv run pytest -x -q`

  Expected: all tests pass

- [ ] **Step 5: Commit**

  ```bash
  git add tests/cli/commands/test_digest.py tests/core/test_pipeline.py
  git commit -m "test: use freeze_time for deterministic date assertions"
  ```

---

### Task 5: Fix test hygiene (ARG005, PLC0415, ARG001, PTH123 in tests)

**Files:**
- Modify: `tests/cli/commands/test_config.py`
- Modify: `tests/cli/commands/test_setup.py`
- Modify: `tests/config/test_loader.py`
- Modify: `tests/cli/commands/test_run.py`

- [ ] **Step 1: Fix `test_config.py` — move `import tomllib` to top**

  `tests/cli/commands/test_config.py` has three inline `import tomllib` statements
  inside test function bodies. The file already imports from `pathlib` and other modules.
  Add `import tomllib` to the top-level imports (it's stdlib in Python 3.11+):

  ```python
  # Add at the top with other stdlib imports:
  import tomllib
  ```

  Then delete all three `import tomllib` lines from inside the test function bodies
  (`test_config_set_updates_value`, `test_config_set_string_value`,
  `test_config_set_updates_value_in_existing_section`).

- [ ] **Step 2: Fix `test_config.py` — `open()` → `Path.open()` and `lambda *_, **__`**

  In the three `assert` blocks that use `open(config_path, "rb")`, replace with
  `config_path.open("rb")`:

  ```python
  # before
  with open(config_path, "rb") as f:
  # after
  with config_path.open("rb") as f:
  ```

  Apply this in `test_config_set_updates_value`, `test_config_set_string_value`,
  and `test_config_set_updates_value_in_existing_section`.

  Also fix the no-op lambda in `test_config_validate_fails_with_missing_env`:
  ```python
  # before
  monkeypatch.setattr("minizen.config.loader.load_dotenv", lambda *a, **k: None)
  # after
  monkeypatch.setattr("minizen.config.loader.load_dotenv", lambda *_, **__: None)
  ```

- [ ] **Step 3: Fix `test_setup.py` — `open()` → `Path.open()`**

  Four occurrences in `tests/cli/commands/test_setup.py` at lines 58, 92, 165, 411.
  In each case, the variable holding the path is `config_path` (a `Path`):

  ```python
  # before
  with open(config_path, "rb") as f:
  # after
  with config_path.open("rb") as f:
  ```

- [ ] **Step 4: Fix `test_loader.py` — unused lambda args**

  In `tests/config/test_loader.py`, the no-op lambda stub:
  ```python
  # before
  monkeypatch.setattr("minizen.config.loader.load_dotenv", lambda *a, **k: None)
  # after
  monkeypatch.setattr("minizen.config.loader.load_dotenv", lambda *_, **__: None)
  ```

- [ ] **Step 5: Fix `test_run.py` — remove unused `mocker` fixture**

  In `tests/cli/commands/test_run.py`, the function
  `test_run_no_config_file_lists_missing_flags` has an unused `mocker: MockerFixture`
  parameter. Remove it:

  ```python
  # before
  def test_run_no_config_file_lists_missing_flags(mocker: MockerFixture) -> None:

  # after
  def test_run_no_config_file_lists_missing_flags() -> None:
  ```

  If `MockerFixture` is now unused in the file, remove it from the `TYPE_CHECKING`
  imports too.

- [ ] **Step 6: Run ruff check — expect zero violations**

  Run: `uv run ruff check 2>&1`

  Expected: no violations (exit code 0)

- [ ] **Step 7: Run tests — expect all pass**

  Run: `uv run pytest -x -q`

  Expected: all tests pass with 100% coverage

- [ ] **Step 8: Commit**

  ```bash
  git add tests/cli/commands/test_config.py tests/cli/commands/test_setup.py \
          tests/config/test_loader.py tests/cli/commands/test_run.py
  git commit -m "fix(ruff): clean up test hygiene (ARG, PLC, PTH violations)"
  ```
