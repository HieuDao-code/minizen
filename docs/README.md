# minizen — A quieter way to stay informed

**minizen** fetches your unread RSS articles from [Miniflux](https://miniflux.app),
uses AI to curate and summarise the most interesting ones, and emails you a clean daily digest.

- **Curated, not firehosed** — the AI picks your top N articles and writes a cohesive
  narrative, not a bullet dump
- **Runs on a schedule** — ships with a GitHub Actions workflow for a hands-free daily digest,
  no server required
- **Dry-run friendly** — preview the digest in your terminal before a single email is sent
- **Pluggable AI** — works with Anthropic Claude or OpenAI models via
  [pydantic-ai](https://ai.pydantic.dev/)

## Quick start

```bash
uv tool install minizen
minizen setup            # interactive wizard — configure Miniflux, AI, and email
minizen digest preview   # preview today's digest in your terminal
minizen run              # fetch → summarise → send
```

→ [Getting Started](getting_started.md) for full setup instructions

→ [How It Works](how_it_works.md) for the architecture
