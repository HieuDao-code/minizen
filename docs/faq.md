# FAQ

## What RSS readers are supported?

minizen supports [Miniflux](https://miniflux.app) only — either the hosted version at
[reader.miniflux.app](https://reader.miniflux.app) or a self-hosted instance.

## Which AI providers and models work?

minizen uses [pydantic-ai](https://ai.pydantic.dev/) under the hood,
so any provider it supports will work. Tested providers:

- **Anthropic** — set `model = "anthropic:claude-haiku-4-5"` and provide `ANTHROPIC_API_KEY`
- **OpenAI** — set `model = "openai:gpt-4o-mini"` and provide `OPENAI_API_KEY`

See the [Configuration reference](configuration.md) for the full list of env vars.

## Can I use a non-Gmail SMTP server?

Yes. minizen uses standard STARTTLS SMTP. Set `smtp_host`, `smtp_port`,
`MINIZEN_EMAIL_USERNAME`, and `MINIZEN_EMAIL_PASSWORD` for any SMTP provider
(Fastmail, Outlook, Mailgun, Postmark, etc.).

## What happens if there are no recent articles?

minizen exits cleanly with a log message — no email is sent.

## How do I test the digest without sending a real email?

Three commands let you run progressively more of the pipeline:

```bash
# Fetch articles only — no AI, no email
minizen digest fetch

# Generate the digest in your terminal — no email sent
minizen digest preview

# Send to your inbox as a test
minizen digest send-test
```

Add `--dry-run` to skip all external side-effects (useful in CI or scripting).

## The digest didn't arrive — what should I check?

1. Run `minizen config validate` to check your settings.
2. Run `minizen digest fetch` to confirm articles are being fetched from Miniflux.
3. Check your spam or junk folder.
4. For Gmail: verify your App Password is correct and 2-Step Verification is enabled.
5. Try `minizen digest send-test` and watch the logs for SMTP errors.
