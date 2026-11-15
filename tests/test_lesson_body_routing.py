import unittest
from types import SimpleNamespace
from unittest.mock import patch

from automation.editorial_agent import worker


class LessonBodyRoutingTests(unittest.TestCase):
    def test_blank_subject_lesson_with_photos_uses_lesson_pipeline(self):
        message = SimpleNamespace(uid="77", from_="author@example.com", subject="", text="Lição 07", html="", attachments=[SimpleNamespace(filename="page.jpg", content_type="image/jpeg")])
        lesson = SimpleNamespace(number=7, slug="2026-t4-licao-07")
        with (
            patch.object(worker, "request_authorization_if_needed", return_value=True),
            patch.object(worker, "publish_lesson_from_message", return_value=lesson) as publish_lesson,
            patch.object(worker, "refine_with_openai") as refine,
            patch.object(worker, "mark_seen") as seen,
        ):
            self.assertTrue(worker.process_article_message(message))
            self.assertEqual(publish_lesson.call_args.args[0].subject, "Lição 07")
            self.assertEqual(message.subject, "")
            refine.assert_not_called()
            seen.assert_called_once_with("artigo@verbovivo.blog", "77")

    def test_text_only_lesson_does_not_trigger_photo_publisher(self):
        message = SimpleNamespace(uid="78", from_="author@example.com", subject="", text="Lição 07", html="", attachments=[])
        with (
            patch.object(worker, "request_authorization_if_needed", return_value=True),
            patch.object(worker, "refine_with_openai", side_effect=RuntimeError("article path")) as refine,
            patch.object(worker, "publish_lesson_from_message") as lesson,
        ):
            with self.assertRaisesRegex(RuntimeError, "article path"):
                worker.process_article_message(message)
            refine.assert_called_once()
            lesson.assert_not_called()
