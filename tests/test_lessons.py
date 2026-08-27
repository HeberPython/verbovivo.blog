from __future__ import annotations

import unittest

from automation.editorial_agent.lessons import (
    DailyReading,
    LessonSummary,
    LessonTopic,
    is_lesson_subject,
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


if __name__ == "__main__":
    unittest.main()
