from types import SimpleNamespace
import unittest
from unittest.mock import patch

from automation.editorial_agent import worker


class PublishMailFlagTests(unittest.TestCase):
    def test_already_published_mail_is_marked_only_if_unread(self):
        message = SimpleNamespace(uid='42', from_='autor@example.com', subject='Artigo existente')
        for unread, expected_calls in [(False, 0), (True, 1)]:
            with self.subTest(unread=unread):
                with (
                    patch.object(worker, 'unread_publish_messages', return_value=[message] if unread else []),
                    patch.object(worker, 'recent_publish_messages', return_value=[message]),
                    patch.object(worker, 'request_authorization_if_needed', return_value=True),
                    patch.object(worker, 'article_publication_status', return_value=True),
                    patch.object(worker, 'mark_seen') as mark,
                    patch.object(worker, 'publish_message_by_uid') as fetch_body,
                    patch.object(worker, 'publish_article') as publish,
                ):
                    worker.publish_once()
                    self.assertEqual(mark.call_count, expected_calls)
                    if unread:
                        mark.assert_called_once_with('publicar@verbovivo.blog', '42')
                    fetch_body.assert_not_called()
                    publish.assert_not_called()
