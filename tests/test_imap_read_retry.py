import ssl
import unittest
from unittest.mock import Mock, patch

from automation.editorial_agent.mail import _fetch_read_only


class ImapReadRetryTests(unittest.TestCase):
    def test_ssl_disconnect_reconnects_without_changing_flags(self):
        mailbox = Mock()
        mailbox.fetch.return_value = ['message']
        with patch('automation.editorial_agent.mail.MailBox', side_effect=[ssl.SSLEOFError('closed'), mailbox]) as factory, \
             patch('automation.editorial_agent.mail.time.sleep'):
            self.assertEqual(_fetch_read_only('host', 993, 'user', 'password', limit=25, headers_only=True), ['message'])
        self.assertEqual(factory.call_count, 2)
        mailbox.fetch.assert_called_once_with(mark_seen=False, limit=25, headers_only=True)
        mailbox.logout.assert_called_once()

    def test_partial_fetch_is_discarded_not_duplicated(self):
        first, second = Mock(), Mock()
        def interrupted():
            yield 'message'
            raise ConnectionResetError('closed')
        first.fetch.return_value = interrupted()
        second.fetch.return_value = ['message', 'next']
        with patch('automation.editorial_agent.mail.MailBox', side_effect=[first, second]), \
             patch('automation.editorial_agent.mail.time.sleep'):
            self.assertEqual(_fetch_read_only('host', 993, 'user', 'password'), ['message', 'next'])
        first.logout.assert_called_once()

    def test_persistent_failure_still_fails_after_three_attempts(self):
        with patch('automation.editorial_agent.mail.MailBox', side_effect=TimeoutError('timeout')) as factory, \
             patch('automation.editorial_agent.mail.time.sleep'):
            with self.assertRaises(TimeoutError):
                _fetch_read_only('host', 993, 'user', 'password')
        self.assertEqual(factory.call_count, 3)

    def test_certificate_error_is_not_retried(self):
        with patch('automation.editorial_agent.mail.MailBox', side_effect=ssl.SSLCertVerificationError('certificate')) as factory:
            with self.assertRaises(ssl.SSLCertVerificationError):
                _fetch_read_only('host', 993, 'user', 'password')
        self.assertEqual(factory.call_count, 1)

    def test_authentication_failure_is_not_retried(self):
        mailbox = Mock()
        mailbox.login.side_effect = ValueError('authentication rejected')
        with patch('automation.editorial_agent.mail.MailBox', return_value=mailbox) as factory:
            with self.assertRaises(ValueError):
                _fetch_read_only('host', 993, 'user', 'password')
        self.assertEqual(factory.call_count, 1)

    def test_logout_failure_does_not_repeat_successful_fetch(self):
        mailbox = Mock()
        mailbox.fetch.return_value = ['message']
        mailbox.logout.side_effect = ssl.SSLEOFError('closed')
        with patch('automation.editorial_agent.mail.MailBox', return_value=mailbox) as factory:
            self.assertEqual(_fetch_read_only('host', 993, 'user', 'password'), ['message'])
        self.assertEqual(factory.call_count, 1)
