"""End-to-end digest pipeline: fetch recent articles, summarise, and email."""

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from minizen.ai.agent import DigestAgent
from minizen.providers.email.smtp import EmailProvider
from minizen.providers.email.template import render_email
from minizen.providers.rss.miniflux import MinifluxProvider

if TYPE_CHECKING:
    from minizen.config.models import Settings

logger = logging.getLogger(__name__)


def run_pipeline(*, settings: Settings, dry_run: bool = False) -> None:
    """Fetch recent articles, generate a digest, and email it.

    Args:
        settings: Fully loaded application settings (Miniflux, email, AI config).
        dry_run: When ``True``, fetch articles but skip the LLM call and email send.
            Logs a summary instead.
    """
    logger.info("Fetching recent articles from Miniflux")
    rss = MinifluxProvider(config=settings.miniflux)
    articles = rss.fetch_recent()
    if not articles:
        logger.info("No recent articles found, nothing to do")
        return

    logger.info("Found %d article(s)", len(articles))

    if dry_run:
        logger.info(
            "Dry run: %d article(s) fetched. LLM and email skipped.",
            len(articles),
        )
        return

    email = EmailProvider(config=settings.email)
    agent = DigestAgent(
        model=settings.ai.model,
        top_n=settings.ai.top_n,
        max_words_per_article=settings.ai.max_words_per_article,
        interests=settings.ai.interests,
        avoid=settings.ai.avoid,
        preferred_categories=settings.ai.preferred_categories,
    )
    result = agent.run(articles=articles)
    selected_ids = set(result.articles_used)
    extra_articles = [a for a in articles if a.id not in selected_ids]
    html, plain_text = render_email(result.markdown, extra_articles=extra_articles)
    today = datetime.now(tz=UTC).date().strftime("%B %-d, %Y")
    logger.info("Sending digest email to %s", settings.email.to_addr)
    email.send(subject=f"Your Daily Zen — {today}", html=html, plain_text=plain_text)
    logger.info("Digest sent successfully")
