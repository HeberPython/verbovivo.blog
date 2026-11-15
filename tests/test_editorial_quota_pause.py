import unittest
from types import SimpleNamespace
from unittest.mock import patch

from automation.editorial_agent import worker
from automation.editorial_agent.text_quality import EditorialQuotaUnavailableError, EditorialTextError


class EditorialQuotaPauseTests(unittest.TestCase):
    def test_exhausted_credits_preserve_unread_and_stop_batch_without_failure(self):
        messages = [SimpleNamespace(uid="1"), SimpleNamespace(uid="2")]
        with (
            patch.object(worker, "unread_messages", return_value=messages),
            patch.object(worker, "process_article_message", side_effect=EditorialQuotaUnavailableError("quota")) as process,
            patch.object(worker, "mark_seen") as mark,
        ):
            worker.poll_once()
            process.assert_called_once_with(messages[0])
            mark.assert_not_called()

    def test_other_editorial_errors_still_fail_job(self):
        message = SimpleNamespace(uid="1")
        with (
            patch.object(worker, "unread_messages", return_value=[message]),
            patch.object(worker, "process_article_message", side_effect=EditorialTextError("invalid text")),
        ):
            with self.assertRaises(EditorialTextError):
                worker.poll_once()
