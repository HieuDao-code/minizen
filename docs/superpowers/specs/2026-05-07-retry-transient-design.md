# Retry on Transient Failure — Design Spec

**Date:** 2026-05-07
**Status:** Approved

## Overview

Add automatic retry with exponential backoff and jitter for transient network errors from the Miniflux API and SMTP provider. Permanent errors (auth failures, bad recipients, 4xx HTTP) are not retried. The feature uses [tenacity](https://tenacity.readthedocs.io/) as the retry library.

## Architecture

### New module: `src/minizen/retry.py`

A single factory function `retry_transient(is_transient)` returns a pre-configured tenacity decorator. All retry policy parameters live here:

- **Attempts:** 3 (initial attempt + 2 retries)
- **Wait:** `wait_exponential_jitter(initial=1, max=30)` — exponential backoff starting at ~1 s, capped at ~30 s, with jitter to avoid thundering herd
- **Retry condition:** `retry_if_exception(is_transient)` — caller-supplied predicate
- **Sleep logging:** `before_sleep_log(logger, WARNING)` — logs each retry attempt at WARNING level

### `MinifluxProvider` (`src/minizen/providers/rss/miniflux.py`)

`fetch_recent()` is decorated with `@retry_transient(is_transient_miniflux)`.

Transient predicate returns `True` for:
- `OSError` (network timeout, connection refused)
- `miniflux.ClientError` where the HTTP status code is 5xx

Returns `False` (permanent, do not retry) for:
- `miniflux.ClientError` with 4xx status (including 401 Unauthorized, 403 Forbidden, 404 Not Found)

After all retries are exhausted, tenacity raises `RetryError`. This is caught inside `fetch_recent()` and re-raised as `MinifluxError` so callers see no interface change.

### `EmailProvider` (`src/minizen/providers/email/smtp.py`)

`send()` is decorated with `@retry_transient(is_transient_smtp)`.

Transient predicate returns `True` for:
- `OSError` (network-level failure)
- `smtplib.SMTPConnectError` (cannot reach server)
- `smtplib.SMTPServerDisconnected` (connection dropped mid-session)

Returns `False` (permanent, do not retry) for:
- `smtplib.SMTPAuthenticationError`
- `smtplib.SMTPRecipientsRefused`
- All other `smtplib.SMTPException` subclasses

After all retries are exhausted, tenacity raises `RetryError`. This is caught inside `send()` and re-raised as `EmailError`.

## Dependencies

Add `tenacity` to `pyproject.toml` project dependencies.

## Error Handling

The existing `MinifluxError` / `EmailError` exception hierarchy is unchanged. Callers (e.g. `run_pipeline`) see identical exception types whether the failure was immediate or after exhausted retries.

## Testing

- **`tests/test_retry.py`** — unit tests for `retry_transient`: verifies the decorator retries the correct number of times, stops on permanent errors, and raises the original exception type after exhaustion.
- **`tests/providers/rss/test_miniflux.py`** — tests for `is_transient_miniflux`: covers OSError, 5xx ClientError (retried), 4xx ClientError (not retried).
- **`tests/providers/email/test_smtp.py`** — tests for `is_transient_smtp`: covers OSError, SMTPConnectError, SMTPServerDisconnected (retried), SMTPAuthenticationError, SMTPRecipientsRefused (not retried).
- Provider retry integration tests: patch the underlying call to fail N times then succeed, assert the result is returned; patch to always fail, assert the correct `MinizenError` subclass is raised.
