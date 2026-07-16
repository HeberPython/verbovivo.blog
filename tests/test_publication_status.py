import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from automation.editorial_agent.models import ArticleDraft
from automation.editorial_agent import publisher
from automation.editorial_agent.publisher import article_publication_status, prefer_ipv4, review_draft_is_available


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

    def test_review_draft_must_render_review_page(self):
        with patch(
            "automation.editorial_agent.publisher.remote_text",
            return_value="<title>Revisão editorial | Verbo Vivo</title>",
        ):
            self.assertTrue(review_draft_is_available("token-ok"))

    def test_review_draft_rejects_missing_message(self):
        with patch(
            "automation.editorial_agent.publisher.remote_text",
            return_value="Rascunho nao encontrado.",
        ):
            self.assertFalse(review_draft_is_available("token-ausente"))

    def test_new_featured_article_keeps_previous_featured_in_grid(self):
        draft = ArticleDraft(
            id="novo",
            token="token",
            sender="",
            source_subject="Novo",
            source_text="",
            title="Novo destaque",
            slug="novo-destaque",
            excerpt="Resumo",
            category="Reflexão",
            author="Autor",
            body_html="",
            image_prompt="",
            image_filename="novo.jpg",
            created_at="2026-07-16T12:00:00+00:00",
        )
        with TemporaryDirectory() as temp:
            site_dir = Path(temp)
            (site_dir / "index.html").write_text(
                '<main><article class="featured"><a href="artigos/antigo.html">'
                '<img src="images/articles/antigo.jpg" alt="Antigo" /></a>'
                '<div class="article-body"><p class="category">Reflexão</p>'
                '<h3><a href="artigos/antigo.html">Antigo</a></h3><p>Resumo antigo</p>'
                '</div></article><section class="article-grid" aria-label="Lista de artigos"></section></main>',
                encoding="utf-8",
            )
            original_site_dir = publisher.SITE_DIR
            publisher.SITE_DIR = site_dir
            try:
                publisher.update_local_indexes(draft)
            finally:
                publisher.SITE_DIR = original_site_dir

            html = (site_dir / "index.html").read_text(encoding="utf-8")
            self.assertIn('class="featured"', html)
            self.assertIn("artigos/novo-destaque.html", html)
            self.assertIn('class="article-card"', html)
            self.assertIn("artigos/antigo.html", html)


if __name__ == "__main__":
    unittest.main()
