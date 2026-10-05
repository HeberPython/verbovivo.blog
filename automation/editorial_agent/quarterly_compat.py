from __future__ import annotations

import re
from html import escape


def install(lessons) -> None:
    """Compatibility fix for quarterly metadata parsing.

    Kept isolated so the quarterly rollout can be validated without rewriting the
    large lessons module through the connector. Remove after the regexes are
    folded directly into lessons.py.
    """

    def card_cycle(card: str) -> tuple[int, int]:
        year_match = re.search(r'data-lesson-year="(20\d{2})"', card)
        quarter_match = re.search(r'data-lesson-quarter="([1-4])"', card)
        if year_match and quarter_match:
            return int(year_match.group(1)), int(quarter_match.group(1))
        return 2026, 3

    original_html_text = lessons.html_text

    def lesson_card_from_html(slug: str, html: str) -> str | None:
        title_match = re.search(r"<h1[^>]*>\s*Lição\s+(\d+)\s*:\s*(.*?)</h1>", html, flags=re.DOTALL | re.IGNORECASE)
        if not title_match:
            title_match = re.search(r"<title[^>]*>\s*Lição\s+(\d+)\s*:\s*(.*?)\s*\|", html, flags=re.DOTALL | re.IGNORECASE)
        if not title_match:
            return None
        number = int(title_match.group(1))
        title = original_html_text(title_match.group(2))
        description_match = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', html, flags=re.IGNORECASE)
        excerpt = original_html_text(description_match.group(1)) if description_match else (
            f"Compêndio retrospectivo da Lição {number}, com texto-chave, leitura bíblica e síntese por tópicos do estudo realizado."
        )
        year_match = re.search(r'<meta\s+name="lesson-year"\s+content="(20\d{2})"', html, flags=re.IGNORECASE)
        quarter_match = re.search(r'<meta\s+name="lesson-quarter"\s+content="([1-4])"', html, flags=re.IGNORECASE)
        slug_cycle = re.match(r"(20\d{2})-t([1-4])-licao-", slug, flags=re.IGNORECASE)
        if year_match and quarter_match:
            year, quarter = int(year_match.group(1)), int(quarter_match.group(1))
        elif slug_cycle:
            year, quarter = int(slug_cycle.group(1)), int(slug_cycle.group(2))
        else:
            year, quarter = 2026, 3
        return f'''\n          <article class="lesson-card" data-lesson-number="{number}" data-lesson-year="{year}" data-lesson-quarter="{quarter}" data-lesson-slug="{escape(slug)}">\n            <div>\n              <p class="category">Lição {number}</p>\n              <h2><a href="licoes/{escape(slug)}.html">{escape(title)}</a></h2>\n              <p>{escape(excerpt)}</p>\n            </div>\n            <a class="lesson-card-link" href="licoes/{escape(slug)}.html">Abrir compêndio</a>\n          </article>\n'''

    lessons.card_cycle = card_cycle
    lessons.lesson_card_from_html = lesson_card_from_html
