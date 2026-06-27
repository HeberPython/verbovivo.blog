import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from automation.editorial_agent import deploy_site
from automation.editorial_agent.models import ArticleDraft


def draft(slug: str, title: str, created_at: str) -> ArticleDraft:
    return ArticleDraft(
        id=slug,
        token="test",
        sender="",
        source_subject=title,
        source_text="",
        title=title,
        slug=slug,
        excerpt=f"Resumo de {title}",
        category="Reflexão Cristã",
        author="Autor",
        body_html="",
        image_prompt="",
        image_filename=f"{slug}.png",
        created_at=created_at,
    )


class CatalogRebuildTests(unittest.TestCase):
    def test_adds_article_navigation_once(self):
        html = (
            '<link rel="stylesheet" href="../styles.css?v=old" />'
            '<p class="publication-date">Publicado em <time>hoje</time>.</p>'
            "</body>"
        )

        updated = deploy_site.with_article_navigation(html)
        updated_twice = deploy_site.with_article_navigation(updated)

        self.assertEqual(updated_twice.count("ARTICLE_NAV_START"), 1)
        self.assertEqual(updated_twice.count("article-navigation.js"), 1)
        self.assertIn("20260627-article-navigation", updated_twice)

    def test_rebuilds_all_indexes_without_losing_articles(self):
        first = draft("mais-recente", "Mais recente", "2026-06-27T12:00:00+00:00")
        second = draft("mais-antigo", "Mais antigo", "2026-06-26T12:00:00+00:00")

        with TemporaryDirectory() as temp:
            site = Path(temp)
            (site / "index.html").write_text(
                '<main><article class="featured">antigo</article>'
                '<section aria-label="Lista" class="article-grid">antigo</section></main>',
                encoding="utf-8",
            )
            (site / "feed.xml").write_text(
                '<?xml version="1.0"?><rss><channel><title>Verbo Vivo</title>'
                "<item><title>Antigo</title></item></channel></rss>",
                encoding="utf-8",
            )
            (site / "sitemap.xml").write_text(
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                "<url><loc>https://verbovivo.blog/</loc></url>"
                "<url><loc>https://verbovivo.blog/artigos/antigo.html</loc></url>"
                "</urlset>",
                encoding="utf-8",
            )
            original_site_dir = deploy_site.SITE_DIR
            deploy_site.SITE_DIR = site
            try:
                deploy_site.rebuild_catalog_indexes([first, second])
            finally:
                deploy_site.SITE_DIR = original_site_dir

            index = (site / "index.html").read_text(encoding="utf-8")
            feed = (site / "feed.xml").read_text(encoding="utf-8")
            sitemap = (site / "sitemap.xml").read_text(encoding="utf-8")
            self.assertIn("artigos/mais-recente.html", index)
            self.assertIn("artigos/mais-antigo.html", index)
            self.assertEqual(feed.count("artigos/mais-recente.html"), 2)
            self.assertEqual(feed.count("artigos/mais-antigo.html"), 2)
            self.assertIn("artigos/mais-recente.html", sitemap)
            self.assertIn("artigos/mais-antigo.html", sitemap)
            self.assertNotIn("artigos/antigo.html", sitemap)

    def test_reads_catalog_metadata_from_json_ld(self):
        metadata = {
            "@type": "BlogPosting",
            "headline": "Título & esperança",
            "description": "Descrição fiel.",
            "image": ["https://verbovivo.blog/images/articles/imagem.png"],
            "datePublished": "2026-06-27T09:00:00+00:00",
            "articleSection": "Reflexão",
            "author": {"name": "Autor"},
        }
        html = (
            '<script type="application/ld+json">'
            + json.dumps(metadata, ensure_ascii=False)
            + "</script>"
        )

        article = deploy_site.article_draft_from_html("slug", html)

        self.assertEqual(article.title, "Título & esperança")
        self.assertEqual(article.image_filename, "imagem.png")
        self.assertEqual(article.created_at, "2026-06-27T09:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
