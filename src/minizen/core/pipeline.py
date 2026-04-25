import mistune

from minizen.ai.agent import DigestAgent
from minizen.config.models import Settings
from minizen.providers.email.smtp import EmailProvider
from minizen.providers.rss.miniflux import MinifluxProvider


def run_pipeline(*, settings: Settings) -> None:
    rss = MinifluxProvider(config=settings.miniflux)
    email = EmailProvider(config=settings.email)
    agent = DigestAgent(model=settings.ai.model, top_n=settings.ai.top_n)

    articles = rss.fetch_unread()
    if not articles:
        return

    result = agent.run(articles=articles)
    html = mistune.html(result.markdown)
    email.send(subject="Your Daily Digest", html=html)
    rss.mark_as_read(article_ids=result.articles_used)
