import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import httpx
from openai import RateLimitError

from automation.editorial_agent.ai import refine_with_openai, request_editorial_completion
from automation.editorial_agent.text_quality import EditorialTextError, validate_reflection
from automation.editorial_agent.worker import process_article_message, poll_once


def rate_error(code):
    response = httpx.Response(429, request=httpx.Request('POST', 'https://api.openai.com/v1/chat/completions'))
    return RateLimitError('not logged', response=response, body={'code': code})


class TextQualityTests(unittest.TestCase):
    def test_eight_email_lines_are_not_a_reflection(self):
        with self.assertRaises(EditorialTextError):
            validate_reflection('original ' * 1600, '<p>Uma frase incompleta e</p>' * 8)

    def test_substantial_complete_text_passes(self):
        validate_reflection('original ' * 1600, ('<p>' + 'Palavra ' * 160 + 'final.</p>') * 3)

    def test_truncated_paragraph_is_blocked_even_if_long(self):
        with self.assertRaises(EditorialTextError):
            validate_reflection('original ' * 1600, ('<p>' + 'Palavra ' * 160 + 'e</p>') * 3)

    def test_quota_fails_without_retry_or_placeholder(self):
        client = Mock()
        client.chat.completions.create.side_effect = rate_error('insufficient_quota')
        with patch('automation.editorial_agent.ai.time.sleep') as sleep:
            with self.assertRaises(EditorialTextError):
                request_editorial_completion(client)
        self.assertEqual(client.chat.completions.create.call_count, 1)
        sleep.assert_not_called()

    def test_temporary_limit_retries_then_succeeds(self):
        client = Mock()
        client.chat.completions.create.side_effect = [rate_error('rate_limit_exceeded'), 'ok']
        with patch('automation.editorial_agent.ai.time.sleep'):
            self.assertEqual(request_editorial_completion(client), 'ok')

    def test_temporary_failure_is_bounded(self):
        client = Mock()
        client.chat.completions.create.side_effect = rate_error('rate_limit_exceeded')
        with patch('automation.editorial_agent.ai.time.sleep'):
            with self.assertRaises(EditorialTextError):
                request_editorial_completion(client)
        self.assertEqual(client.chat.completions.create.call_count, 3)

    def test_missing_key_never_creates_placeholder(self):
        with patch('automation.editorial_agent.ai.settings', SimpleNamespace(openai_api_key='')):
            with self.assertRaises(EditorialTextError):
                refine_with_openai('original', 'subject', 'sender')

    def test_failure_leaves_email_unread_and_does_not_send_review_or_image(self):
        message = SimpleNamespace(from_='author@example.com', subject='A BOA OBRA', text='original', uid='123')
        with patch('automation.editorial_agent.worker.request_authorization_if_needed', return_value=True), \
             patch('automation.editorial_agent.worker.refine_with_openai', side_effect=EditorialTextError('failed')), \
             patch('automation.editorial_agent.worker.generate_cover_image') as image, \
             patch('automation.editorial_agent.worker.send_review_email') as mail, \
             patch('automation.editorial_agent.worker.mark_seen') as seen:
            with self.assertRaises(EditorialTextError):
                process_article_message(message)
        image.assert_not_called()
        mail.assert_not_called()
        seen.assert_not_called()

    def test_failed_message_does_not_block_other_messages(self):
        with patch('automation.editorial_agent.worker.unread_messages', return_value=[1, 2]), \
             patch('automation.editorial_agent.worker.process_article_message', side_effect=[EditorialTextError('failed'), True]) as process:
            with self.assertRaises(EditorialTextError):
                poll_once()
        self.assertEqual(process.call_count, 2)


if __name__ == '__main__':
    unittest.main()
