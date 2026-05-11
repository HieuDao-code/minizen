# Implementation TODOs

### Short-term:

- [ ] Check how to optimize tokens. Fetch original content?
- [ ] Build a ranking + filtering system

### Long-term:

- Implement more LLM models provider
- Add additional filtering options, such as keywords, add more articles but as additional entries which only contain the title and link without the summary (or a one sentence summary) at the end.
- Some type of critera and rules for articles to be set to read if they got not picked in the digest, so next time they will excluded

### Out of scope for now but maybe in the future:

- more ai assistant features like:
  - quote of the day, favourite quote
  - weather forecast
  - personal goals and reminders

# minizen — Feature Backlog

## Ideas backlog

### Configurable lookback window

Allow `lookback_hours` in `[ai]` config (or as a CLI flag) so the tool can run as a weekly digest (`lookback_hours = 168`) rather than always pulling the last 24h.

### Feed category filtering

Add `include_categories` and/or `exclude_categories` lists to `[miniflux]` config so users can pull articles only from specific Miniflux categories instead of everything.

### Article deduplication

Track which article IDs have already appeared in past digests (e.g. a local state file) so the same article is never included twice across runs.
