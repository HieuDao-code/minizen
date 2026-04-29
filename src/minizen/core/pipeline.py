"""End-to-end digest pipeline: fetch articles, summarise, email, mark as read."""

import logging
from datetime import date
from typing import TYPE_CHECKING

from minizen.ai.agent import DigestAgent
from minizen.providers.email.smtp import EmailProvider
from minizen.providers.email.template import render_email
from minizen.providers.rss.miniflux import MinifluxProvider

if TYPE_CHECKING:
    from minizen.config.models import Settings

logger = logging.getLogger(__name__)


def run_pipeline(*, settings: Settings, dry_run: bool = False) -> None:
    """Fetch unread articles, generate a digest, email it, then mark articles as read.

    Args:
        settings: Fully loaded application settings (Miniflux, email, AI config).
        dry_run: When ``True``, fetch articles but skip the LLM call, email send,
            and mark-as-read. Logs a summary instead.
    """
    logger.info("Fetching unread articles from Miniflux")
    rss = MinifluxProvider(config=settings.miniflux)
    articles = rss.fetch_unread()
    if not articles:
        logger.info("No unread articles found, nothing to do")
        return

    logger.info("Found %d article(s)", len(articles))

    if dry_run:
        logger.info(
            "Dry run: %d article(s) fetched. LLM, email, and mark-as-read skipped.",
            len(articles),
        )
        return

    email = EmailProvider(config=settings.email)
    agent = DigestAgent(model=settings.ai.model, top_n=settings.ai.top_n)
    result = agent.run(articles=articles)
    html, plain_text = render_email(result.markdown)
    today = date.today().strftime("%B %-d, %Y")
    logger.info("Sending digest email to %s", settings.email.to_addr)
    email.send(subject=f"Your Daily Zen — {today}", html=html, plain_text=plain_text)
    logger.info("Marked %d article(s) as read", len(result.articles_used))
    rss.mark_as_read(article_ids=result.articles_used)
