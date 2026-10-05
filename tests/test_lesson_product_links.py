from __future__ import annotations

import unittest

from automation.editorial_agent.lesson_product_links import (
    LEGACY_PRODUCT_URL,
    product_url_for_cycle,
)
from automation.editorial_agent.lessons import LessonSummary, render_lesson_page


Q4_PRODUCT_URL = "https://www.editorakaleo.com/product-page/revista-ebd-o-deserto-e-a-igreja-aluno"


class LessonProductLinksTests(unittest.TestCase):
    def test_q3_preserves_legacy_magazine(self) -> None:
        self.assertEqual(product_url_for_cycle(2026, 3), LEGACY_PRODUCT_URL)

    def test_q4_uses_deserto_e_igreja_magazine(self) -> None:
        self.assertEqual(product_url_for_cycle(2026, 4), Q4_PRODUCT_URL)

    def test_q4_page_contains_official_magazine_link(self) -> None:
        html = render_lesson_page(LessonSummary(number=1, title="O livro da libertação", year=2026, quarter=4))
        self.assertIn(Q4_PRODUCT_URL, html)
        self.assertNotIn(LEGACY_PRODUCT_URL, html)

    def test_q3_page_keeps_legacy_magazine_link(self) -> None:
        html = render_lesson_page(LessonSummary(number=1, title="Lição legada", year=2026, quarter=3))
        self.assertIn(LEGACY_PRODUCT_URL, html)
        self.assertNotIn(Q4_PRODUCT_URL, html)


if __name__ == "__main__":
    unittest.main()
