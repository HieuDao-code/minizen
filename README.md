<h1 align="center"><p align="center">
  <span style="font-size: 80px; font-weight: bold; color: #FFA500;">minizen</span>
</p></h1>
<p align="center">A quieter way to stay informed.</p>
<p align="center">
  <a href="https://hieudao-code.github.io/minizen/">Documentation</a> | <a href="https://hieudao-code.github.io/minizen/getting_started/">Getting Started</a> | <a href="https://hieudao-code.github.io/minizen/configuration/">Configuration</a>
</p>

## About

**minizen** fetches your unread RSS articles from [Miniflux](https://miniflux.app),
uses AI to curate and summarise the most interesting ones, and emails you a clean daily digest.


### Features

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
