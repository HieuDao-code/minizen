# More to Read — Feed Name Labels Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a feed-name badge above each linked title in the "More to read" section of the digest email.

**Architecture:** Two edits in a single file: (1) the `_build_more_links` Python function emits a `<span class="feed-badge">` per list item, (2) two CSS rules inside `render_email` make the badge stack above its link.

**Tech Stack:** Python 3.12, mistune, pytest, pytest-mock

---

## File Map

| Action | Path |
|--------|------|
| Modify | `src/minizen/providers/email/template.py` — `_build_more_links` function and CSS block inside `render_email` |
| Modify | `tests/providers/email/test_template.py` — add two new tests |

---

### Task 1: Test that feed name appears in "More to read" items

**Files:**
- Modify: `tests/providers/email/test_template.py`

- [ ] **Step 1: Write the failing test**

Open `tests/providers/email/test_template.py`. Add this test after `test_render_email_with_extra_articles_shows_link_list`:

```python
def test_render_email_shows_feed_name_in_more_links() -> None:
    # arrange
    extra = Article(
        id=99,
        title="Extra Article Title",
        url="https://example.com/extra",
        content="content",
        feed_name="My Source Feed",
        published_at=datetime(2026, 5, 4, tzinfo=UTC),
    )

    # act
    html, _ = render_email(markdown="## Hello", extra_articles=[extra])

    # assert
    assert "My Source Feed" in html
    assert 'class="feed-badge"' in html
```

- [ ] **Step 2: Run the test to confirm it fails**

```bash
uv run pytest tests/providers/email/test_template.py::test_render_email_shows_feed_name_in_more_links -v
```

Expected: FAIL — `"My Source Feed" not in html` (feed name not currently rendered in `_build_more_links`).

- [ ] **Step 3: Write a test that the feed name is HTML-escaped**

Still in `tests/providers/email/test_template.py`, add:

```python
def test_render_email_escapes_feed_name_in_more_links() -> None:
    # arrange
    extra = Article(
        id=4,
        title="Normal Title",
        url="https://example.com/article",
        content="content",
        feed_name='<script>alert("xss")</script>',
        published_at=datetime(2026, 5, 6, tzinfo=UTC),
    )

    # act
    html, _ = render_email(markdown="Hello", extra_articles=[extra])

    # assert
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
```

- [ ] **Step 4: Run both new tests to confirm both fail**

```bash
uv run pytest tests/providers/email/test_template.py::test_render_email_shows_feed_name_in_more_links tests/providers/email/test_template.py::test_render_email_escapes_feed_name_in_more_links -v
```

Expected: both FAIL.

---

### Task 2: Implement feed-name badge in `_build_more_links`

**Files:**
- Modify: `src/minizen/providers/email/template.py`

- [ ] **Step 1: Update `_build_more_links`**

In `src/minizen/providers/email/template.py`, replace the current `_build_more_links` function (lines 74–93) with:

```python
def _build_more_links(articles: list[Article]) -> str:
    """Build a compact "More to read" link list for articles without full summaries.

    Each item shows a feed-name badge above the linked article title.

    Args:
        articles: Articles to list. Returns an empty string when the list is empty.

    Returns:
        An HTML ``<div>`` containing a heading and ``<ul>`` of badge + linked titles,
        or an empty string if ``articles`` is empty.
    """
    if not articles:
        return ""
    items = "".join(
        f'<li>'
        f'<span class="feed-badge">{escape(a.feed_name)}</span>'
        f'<a href="{escape(a.url)}">{escape(a.title)}</a>'
        f"</li>"
        for a in articles
        if a.url.startswith(("https://", "http://"))
    )
    if not items:
        return ""
    return f'<div class="more-links"><h3>More to read</h3><ul>{items}</ul></div>'
```

- [ ] **Step 2: Run the two new tests — expect both to pass**

```bash
uv run pytest tests/providers/email/test_template.py::test_render_email_shows_feed_name_in_more_links tests/providers/email/test_template.py::test_render_email_escapes_feed_name_in_more_links -v
```

Expected: both PASS.

- [ ] **Step 3: Run the full template test suite — expect no regressions**

```bash
uv run pytest tests/providers/email/test_template.py -v
```

Expected: all tests PASS.

---

### Task 3: Add CSS rules to stack the badge above the link

**Files:**
- Modify: `src/minizen/providers/email/template.py` — CSS block inside `render_email`

- [ ] **Step 1: Add two CSS rules to the `.more-links` block**

In `src/minizen/providers/email/template.py`, locate the `.more-links li` rule inside the `<style>` block (currently around line 261):

```css
    .more-links li {{
      margin-bottom: 6px;
      font-size: 14px;
    }}
```

Replace it with:

```css
    .more-links li {{
      margin-bottom: 12px;
      font-size: 14px;
    }}
    .more-links .feed-badge {{
      display: block;
    }}
```

- [ ] **Step 2: Run the full template test suite — expect all tests still pass**

```bash
uv run pytest tests/providers/email/test_template.py -v
```

Expected: all tests PASS.

- [ ] **Step 3: Run the full test suite**

```bash
uv run pytest -v
```

Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add src/minizen/providers/email/template.py tests/providers/email/test_template.py
git commit -m "feat: show feed name badge in More to Read section"
```

---

## Self-Review

**Spec coverage:**
- ✅ Feed name badge (`<span class="feed-badge">`) above linked title in each `<li>` — Task 2
- ✅ HTML-escape feed name — Task 2 (uses `escape()` already imported)
- ✅ `display: block` on `.more-links .feed-badge` — Task 3
- ✅ Increased `<li>` spacing (`margin-bottom: 12px`) — Task 3
- ✅ Section title stays "More to read" — no change required
- ✅ Tests for new behavior — Task 1

**No placeholders, no type inconsistencies.**
