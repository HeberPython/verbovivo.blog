from __future__ import annotations

import unittest

from automation.editorial_agent.lessons import (
    DailyReading,
    LessonSummary,
    LessonTopic,
    active_lesson_cycle,
    is_lesson_subject,
    lesson_cycle_from_subject,
    lesson_card,
    lesson_card_from_html,
    lesson_number_from_subject,
    merge_lesson_card,
    render_lesson_page,
)


class LessonWorkflowTests(unittest.TestCase):
    def test_lesson_subject_detection_accepts_accent_and_padding(self) -> None:
        self.assertTrue(is_lesson_subject("Lição 01"))
        self.assertEqual(lesson_number_from_subject("Licao 13 - trimestre"), 13)

    def test_lesson_subject_detection_rejects_normal_article(self) -> None:
        self.assertFalse(is_lesson_subject("A coroa da virtude"))
        self.assertIsNone(lesson_number_from_subject("REFERENCIAS"))

    def test_render_lesson_page_uses_retroactive_compendium_language(self) -> None:
        lesson = LessonSummary(
            number=1,
            title="Chamados para aprender",
            series="Jesus, o Glorioso Salvador",
            key_text="Mateus, capítulo 7, versículo 29.",
            daily_wisdom=[DailyReading(day="Segunda-feira", summary="Jesus ensina", reference="Mateus, capítulo 4, versículo 23.")],
            bible_reading="Mateus, capítulo 7, versículos 28 e 29.",
            topics=[LessonTopic(heading="1. O ensino de Jesus", summary="Síntese fiel do tópico.")],
        )
        html = render_lesson_page(lesson)
        self.assertIn("Compêndio retrospectivo", html)
        self.assertIn("já estudada na Escola Bíblica Dominical", html)
        self.assertIn("Comprar esta revista", html)

    def test_lesson_card_shows_only_lesson_number(self) -> None:
        lesson = LessonSummary(
            number=3,
            title="Jesus e os Ritos Judaicos",
            series="Jesus — O Glorioso Salvador",
        )

        card = lesson_card(lesson)

        self.assertIn('<p class="category">Lição 3</p>', card)
        self.assertNotIn("Glorioso Salvador", card)

    def test_lesson_card_from_html_shows_only_lesson_number(self) -> None:
        html = """
        <html>
          <head>
            <title>Lição 3: Jesus e os Ritos Judaicos | Lições Escola Dominical</title>
            <meta name="description" content="Compêndio retrospectivo da Lição 3." />
          </head>
          <body>
            <h1>Lição 3: Jesus e os Ritos Judaicos</h1>
            <p class="series">Jesus — O Glorioso Salvador</p>
          </body>
        </html>
        """

        card = lesson_card_from_html("licao-3-jesus-e-os-ritos-judaicos", html)

        self.assertIsNotNone(card)
        self.assertIn('<p class="category">Lição 3</p>', card or "")
        self.assertNotIn("Glorioso Salvador", card or "")

    def test_merge_lesson_card_replaces_same_lesson(self) -> None:
        html = """
        <section class="lesson-list" aria-label="Lições publicadas">
          <article class="lesson-card" data-lesson-number="1" data-lesson-slug="licao-1-antiga"><h2>Antiga</h2></article>
        </section>
        """
        updated = merge_lesson_card(
            html,
            '<article class="lesson-card" data-lesson-number="1" data-lesson-slug="licao-1-antiga"><h2>Nova</h2></article>',
            1,
        )
        self.assertIn("Nova", updated)
        self.assertNotIn("Antiga", updated)
        self.assertEqual(updated.count('data-lesson-number="1"'), 1)

    def test_merge_lesson_card_preserves_different_cycle_same_number(self) -> None:
        html = """
        <section class="lesson-list" aria-label="Lições publicadas">
          <article class="lesson-card" data-lesson-number="1" data-lesson-slug="licao-1-ciclo-antigo"><h2>Ciclo antigo</h2></article>
        </section>
        """
        updated = merge_lesson_card(
            html,
            '<article class="lesson-card" data-lesson-number="1" data-lesson-slug="licao-1-ciclo-novo"><h2>Ciclo novo</h2></article>',
            1,
        )
        self.assertIn("Ciclo antigo", updated)
        self.assertIn("Ciclo novo", updated)
        self.assertEqual(updated.count('data-lesson-number="1"'), 2)


    def test_active_cycle_defaults_to_2026_q4(self) -> None:
        self.assertEqual(active_lesson_cycle("Lição 01"), (2026, 4))

    def test_explicit_matching_cycle_is_accepted(self) -> None:
        self.assertEqual(lesson_cycle_from_subject("Lição 01 - 4º Trimestre 2026"), (2026, 4))
        self.assertEqual(active_lesson_cycle("Lição 01 - 4º Trimestre 2026"), (2026, 4))

    def test_explicit_conflicting_cycle_aborts(self) -> None:
        with self.assertRaises(RuntimeError):
            active_lesson_cycle("Lição 01 - 3º Trimestre 2026")

    def test_quarterly_slug_prevents_same_number_collision(self) -> None:
        old = LessonSummary(number=1, title="Mesmo título", year=2026, quarter=3)
        new = LessonSummary(number=1, title="Mesmo título", year=2026, quarter=4)
        future = LessonSummary(number=1, title="Mesmo título", year=2027, quarter=1)
        self.assertNotEqual(old.slug, new.slug)
        self.assertNotEqual(new.slug, future.slug)
        self.assertTrue(new.slug.startswith("2026-t4-licao-01-"))

    def test_legacy_page_is_classified_as_2026_q3_without_changing_url(self) -> None:
        html = """
        <html><head><title>Lição 1: Antiga | Lições Escola Dominical</title></head>
        <body><h1>Lição 1: Antiga</h1></body></html>
        """
        card = lesson_card_from_html("licao-1-antiga", html) or ""
        self.assertIn('data-lesson-year="2026"', card)
        self.assertIn('data-lesson-quarter="3"', card)
        self.assertIn('href="licoes/licao-1-antiga.html"', card)

    def test_catalog_groups_q4_before_q3_and_preserves_both_lesson_ones(self) -> None:
        html = """
        <section class="lesson-list" aria-label="Lições publicadas">
          <article class="lesson-card" data-lesson-number="1" data-lesson-year="2026" data-lesson-quarter="3" data-lesson-slug="licao-1-antiga"><h2>Antiga</h2></article>
        </section>
        """
        current = LessonSummary(number=1, title="Nova", year=2026, quarter=4)
        updated = merge_lesson_card(html, lesson_card(current), 1)
        self.assertIn("4º Trimestre de 2026 — Atual", updated)
        self.assertIn("Lições anteriores — 3º Trimestre de 2026", updated)
        self.assertLess(updated.index("4º Trimestre"), updated.index("3º Trimestre"))
        self.assertEqual(updated.count('data-lesson-number="1"'), 2)


if __name__ == "__main__":
    unittest.main()
