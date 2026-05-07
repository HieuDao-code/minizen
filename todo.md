# minizen — Feature Backlog

## Ideas backlog

### Configurable lookback window

Allow `lookback_hours` in `[ai]` config (or as a CLI flag) so the tool can run as a weekly digest (`lookback_hours = 168`) rather than always pulling the last 24h.

### Feed category filtering

Add `include_categories` and/or `exclude_categories` lists to `[miniflux]` config so users can pull articles only from specific Miniflux categories instead of everything.

### Article deduplication

Track which article IDs have already appeared in past digests (e.g. a local state file) so the same article is never included twice across runs.

### Retry on transient failure

Add automatic retry with exponential backoff for transient network errors from the Miniflux API and SMTP provider, instead of failing hard on the first error.
