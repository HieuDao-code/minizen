# Dry Run Flag — Design Spec

**Date:** 2026-04-25
**Status:** Approved

## Problem

Running `minizen run` or `minizen digest send-test` makes real LLM API calls (which cost money) and sends real emails. There is no way to test that the pipeline is wired correctly without incurring those side effects. Users also want to inspect what would happen — how many articles were found, what the rendered email looks like — before committing to a full run.

## Behaviour

### `minizen run --dry-run`

Fetches real articles from Miniflux, then exits early. No LLM call, no email send, no mark-as-read.

Output:
```
Dry run: 12 article(s) fetched. LLM call, email, and mark-as-read skipped.
```

### `minizen digest preview --dry-run`

Fetches real articles from Miniflux, then prints them in the same format as `digest fetch` (title + URL per article). No LLM call.

### `minizen digest send-test` (normal, no flag)

Before making the LLM call, prompts the user:

```
This will make a real LLM API call and send a test email. Continue? [y/N]:
```

- **Yes** → proceeds as before (LLM call + email send).
- **No** → exits cleanly with code 0 (`typer.Abort()`).

### `minizen digest send-test --dry-run`

Skips the confirmation prompt (no cost). Fetches articles, calls LLM, renders the email, then prints the plain-text version to stdout instead of sending. No SMTP call.

Output prefix:
```
Dry run — email not sent:

<plain text of rendered email>
```

### `minizen digest fetch`

No `--dry-run` needed — `fetch` has no side effects and already behaves as a dry run.

## Design

### `core/pipeline.py` — `run_pipeline()`

Add `dry_run: bool = False`. When `True`:
1. Fetch articles from Miniflux (real call).
2. If no articles, exit early as normal.
3. Print dry-run summary and return — skip agent, email, and mark-as-read.

```python
def run_pipeline(*, settings: Settings, dry_run: bool = False) -> None:
    ...
    if dry_run:
        logger.info("Dry run: %d article(s) fetched. LLM call, email, and mark-as-read skipped.", len(articles))
        return
    ...
```

### `cli/commands/run.py`

Add `dry_run: bool` option (`--dry-run`), pass to `run_pipeline(dry_run=dry_run)`.

### `cli/commands/digest.py`

**`preview`**: add `--dry-run`. When `True`, print articles (title + URL) instead of calling the agent.

**`send_test`**: add `--dry-run`.
- When `False` (normal): call `typer.confirm()` before the LLM call. Abort if declined.
- When `True`: skip confirmation, call LLM, render email, print plain text, skip `email.send()`.

## Files Changed

| File | Change |
|---|---|
| `src/minizen/core/pipeline.py` | Add `dry_run: bool = False` parameter; early return with summary message |
| `src/minizen/cli/commands/run.py` | Add `--dry-run` flag; pass to `run_pipeline()` |
| `src/minizen/cli/commands/digest.py` | Add `--dry-run` to `preview` and `send_test`; add confirm prompt to `send_test` |
| `tests/core/test_pipeline.py` | Add dry-run tests |
| `tests/cli/commands/test_run.py` | Add `--dry-run` CLI tests |
| `tests/cli/commands/test_digest.py` | Add dry-run and confirm-prompt tests |

## Tests

| Scenario | Assertion |
|---|---|
| `run_pipeline(dry_run=True)` | agent not called, email not sent, articles not marked read |
| `run_pipeline(dry_run=False)` | existing behaviour unchanged |
| `run --dry-run` CLI | `run_pipeline` called with `dry_run=True` |
| `digest preview --dry-run` | agent not called, article titles/URLs in output |
| `digest send-test` (normal) | confirm prompt shown before LLM call |
| `digest send-test` + confirm "no" | exits cleanly, LLM not called |
| `digest send-test --dry-run` | no confirm prompt, LLM called, email not sent, plain text in output |
