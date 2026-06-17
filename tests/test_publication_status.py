import unittest
from unittest.mock import patch

from automation.editorial_agent.publisher import article_publication_status, prefer_ipv4


class PublicationStatusTests(unittest.TestCase):
    def test_ipv4_preference_filters_ipv6_when_ipv4_exists(self):
        addresses = [
            (10, 1, 6, "", ("::1", 443, 0, 0)),
            (2, 1, 6, "", ("127.0.0.1", 443)),
        ]
        with patch("socket.getaddrinfo", return_value=addresses):
            with prefer_ipv4():
                import socket

                result = socket.getaddrinfo("example.com", 443)
        self.assertEqual([item[0] for item in result], [2])

    def test_returns_unknown_when_remote_site_cannot_be_checked(self):
        with patch(
            "automation.editorial_agent.publisher.remote_text",
            side_effect=RuntimeError("network unavailable"),
        ):
            self.assertIsNone(article_publication_status("artigo-existente"))

    def test_requires_article_home_feed_and_sitemap(self):
        values = {
            "artigos/reflexao.html": "<article>conteudo</article>",
            "index.html": '<a href="artigos/reflexao.html">Reflexao</a>',
            "feed.xml": "https://verbovivo.blog/artigos/reflexao.html",
            "sitemap.xml": "https://verbovivo.blog/artigos/reflexao.html",
        }
        with patch(
            "automation.editorial_agent.publisher.remote_text",
            side_effect=lambda path: values[path],
        ):
            self.assertTrue(article_publication_status("reflexao"))


if __name__ == "__main__":
    unittest.main()
