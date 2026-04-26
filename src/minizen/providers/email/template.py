import math
from datetime import date
from importlib.metadata import version as pkg_version

import mistune


def _reading_time(markdown: str) -> int:
    """Estimate reading time in minutes assuming 200 words per minute.

    Args:
        markdown: Raw Markdown text to measure.

    Returns:
        Estimated reading time in whole minutes, minimum 1.
    """
    words = len(markdown.split())
    return max(1, math.ceil(words / 200))


def render_email(markdown: str) -> tuple[str, str]:
    """Render a Markdown digest into a styled HTML email and a plain-text fallback.

    Args:
        markdown: Raw Markdown digest produced by the AI agent.

    Returns:
        A ``(html, plain_text)`` tuple where ``html`` is a fully styled email
        document and ``plain_text`` is the original Markdown unchanged.
    """
    today = date.today().strftime("%B %-d, %Y")
    read_time = _reading_time(markdown)
    minizen_version = pkg_version("minizen")
    content_html = mistune.html(markdown)
    preheader = f"~{read_time} min read · Your curated articles for {today}"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    body {{ margin:0; padding:0; }}
    img {{ border:0; display:block; }}

    body {{
      background: #F2EFE9;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      color: #2E2A25;
      font-size: 16px;
      line-height: 1.6;
    }}
    .wrapper {{
      max-width: 620px;
      margin: 32px auto;
      background: #FAFAF8;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    }}
    .header {{
      background: linear-gradient(135deg, #F2EFE9 0%, #C8B89A 50%, #9E8A72 100%);
      padding: 36px 32px 28px;
      color: #2E2A25;
    }}
    .header-label {{
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      opacity: 0.65;
      margin: 0 0 8px;
    }}
    .header h1 {{
      margin: 0 0 8px;
      font-size: 28px;
      font-weight: 800;
      line-height: 1.2;
    }}
    .header .meta {{
      margin: 0;
      font-size: 14px;
      opacity: 0.7;
    }}
    .content {{
      padding: 32px 32px 24px;
    }}
    .content h1 {{
      font-size: 22px;
      font-weight: 700;
      color: #2E2A25;
      margin: 28px 0 6px;
      line-height: 1.3;
    }}
    .content h2 {{
      font-size: 18px;
      font-weight: 700;
      color: #2E2A25;
      margin: 36px 0 8px;
      padding-left: 12px;
      border-left: 4px solid #7A9E7E;
      line-height: 1.3;
    }}
    .content p {{
      font-size: 16px;
      line-height: 1.8;
      color: #2E2A25;
      margin: 8px 0 18px;
    }}
    .content a {{
      color: #6B8F6E;
      text-decoration: none;
      font-weight: 500;
    }}
    .content a:hover {{ text-decoration: underline; }}
    .content strong {{ color: #2E2A25; font-weight: 600; }}
    .content em {{ color: #6B6560; }}
    .content hr {{
      border: none;
      border-top: 1px solid #D4CEC8;
      margin: 28px 0;
    }}
    .content ul, .content ol {{
      padding-left: 20px;
      color: #2E2A25;
      font-size: 16px;
      line-height: 1.8;
    }}
    .content blockquote {{
      border-left: 3px solid #C8B89A;
      margin: 16px 0;
      padding: 4px 16px;
      color: #6B6560;
      font-style: italic;
    }}
    .footer {{
      background: #EAE5DC;
      border-top: 1px solid #D4CEC8;
      padding: 20px 32px;
      font-size: 13px;
      color: #6B6560;
      text-align: center;
    }}
    .footer a {{
      color: #7A9E7E;
      text-decoration: none;
      font-weight: 600;
    }}
    .footer .version {{
      display: block;
      margin-top: 4px;
      font-size: 11px;
      opacity: 0.7;
    }}

    @media (max-width: 640px) {{
      .wrapper {{ margin: 0; border-radius: 0; box-shadow: none; }}
      .header {{ padding: 28px 20px 22px; }}
      .header h1 {{ font-size: 24px; }}
      .content {{ padding: 24px 20px 20px; }}
      .content h1 {{ font-size: 20px; }}
      .content h2 {{ font-size: 17px; }}
      .content p, .content ul, .content ol {{ font-size: 17px; line-height: 1.85; }}
      .footer {{ padding: 16px 20px; }}
    }}
  </style>
</head>
<body>
  <span style="display:none;max-height:0;overflow:hidden;mso-hide:all;">{preheader}</span>
  <div class="wrapper">
    <div class="header">
      <p class="header-label">minizen</p>
      <h1>Your Daily Zen</h1>
      <p class="meta">{today} &middot; ~{read_time} min read</p>
    </div>
    <div class="content">
      {content_html}
    </div>
    <div class="footer">
      Curated by <a href="https://hieudao-code.github.io/minizen/">minizen</a> &middot; {today}
      <span class="version">v{minizen_version}</span>
    </div>
  </div>
</body>
</html>"""

    return html, markdown
