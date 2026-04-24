# RSS feed

We create a simple RSS feed reader that summarizes articles using Claude.
After that it sends an email with the highlights of the articles using a simple email client module.

It uses [miniflux](https://github.com/miniflux/python-client) as a RSS feed client and [pydantic-ai](https://github.com/pydantic/pydantic-ai) as the AI summarization module.
