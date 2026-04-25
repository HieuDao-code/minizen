from datetime import date

from minizen.ai.agent import DigestAgent
from minizen.config.models import Settings
from minizen.providers.email.smtp import EmailProvider
from minizen.providers.email.template import render_email
from minizen.providers.rss.miniflux import MinifluxProvider


def run_pipeline(*, settings: Settings) -> None:
    """Fetch unread articles, generate a digest, email it, then mark articles as read.

    Args:
        settings: Fully loaded application settings (Miniflux, email, AI config).
    """
    rss = MinifluxProvider(config=settings.miniflux)
    articles = rss.fetch_unread()
    if not articles:
        return

    email = EmailProvider(config=settings.email)
    agent = DigestAgent(model=settings.ai.model, top_n=settings.ai.top_n)
    result = agent.run(articles=articles)
    html, plain_text = render_email(result.markdown)
    today = date.today().strftime("%B %-d, %Y")
    email.send(subject=f"Your Daily Zen — {today}", html=html, plain_text=plain_text)
    rss.mark_as_read(article_ids=result.articles_used)
