# minizen — Feature Backlog

## Ready to implement

### Interest profile
Add `interests` and `avoid` lists to `[ai]` config so the AI prioritises articles the user cares about and skips topics they don't want.

- Add `interests: list[str]` and `avoid: list[str]` to `AIConfig` (optional, default `[]`)
- Inject a preference block into the AI system prompt when non-empty
- Add interactive prompts + `--interests`/`--avoid` CLI flags to the setup wizard
- Spec: `docs/superpowers/specs/2026-05-06-interest-profile-design.md`

---

## Ideas backlog

### Configurable lookback window
Allow `lookback_hours` in `[ai]` config (or as a CLI flag) so the tool can run as a weekly digest (`lookback_hours = 168`) rather than always pulling the last 24h.

### Feed category filtering
Add `include_categories` and/or `exclude_categories` lists to `[miniflux]` config so users can pull articles only from specific Miniflux categories instead of everything.

### Article deduplication
Track which article IDs have already appeared in past digests (e.g. a local state file) so the same article is never included twice across runs.

### Retry on transient failure
Add automatic retry with exponential backoff for transient network errors from the Miniflux API and SMTP provider, instead of failing hard on the first error.
