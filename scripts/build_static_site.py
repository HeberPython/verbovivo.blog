from __future__ import annotations

import html
import re
import shutil
from datetime import date
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
ARTICLE_DIR = SITE / "artigos"
IMAGE_OUT = SITE / "images" / "articles"
IMAGE_IN = ROOT / "public" / "images" / "articles"
DOMAIN = "https://verbovivo.blog"


ARTICLES = [
    {
        "title": "Depois da Festa: onde ficou Jesus?",
        "slug": "depois-da-festa-onde-ficou-jesus",
        "category": "Vida Cristã",
        "date": "2026-05-10",
        "author": "Heber",
        "pdf": Path(r"C:\Users\Heber\Documents\verbovivo.blog\DEPOIS DA FESTA.pdf"),
        "image": "depois-da-festa.png",
        "alt": "Rua antiga vazia ao anoitecer com ramos no chão e uma casa iluminada ao fundo",
        "excerpt": "Uma reflexão sobre o contraste entre celebrar Cristo em público e acolhê-lo no cotidiano, quando os aplausos cessam.",
    },
    {
        "title": "Feitos para brilhar pela Palavra da Vida",
        "slug": "feitos-para-brilhar-pela-palavra-da-vida",
        "category": "Estudo Bíblico",
        "date": "2026-05-10",
        "author": "Heber",
        "pdf": Path(r"C:\Users\Heber\Documents\verbovivo.blog\FILIPENSES - FEITOS PARA BRILHAR - Palestra - Heber.pdf"),
        "image": "feitos-para-brilhar.png",
        "alt": "Bíblia aberta sobre mesa sob céu estrelado antes do amanhecer",
        "excerpt": "Um estudo em Filipenses 2 sobre murmuração, pureza, testemunho e firme apego à Palavra em uma geração escura.",
    },
    {
        "title": "O coração desordenado",
        "slug": "o-coracao-desordenado",
        "category": "Formação Interior",
        "date": "2026-05-10",
        "author": "Heber",
        "pdf": Path(r"C:\Users\Heber\Documents\verbovivo.blog\LIÇÃO - CORAÇÃO DESORDENADO.pdf"),
        "image": "coracao-desordenado.png",
        "alt": "Mesa de estudo com Bíblia aberta, papéis e vaso de barro rachado derramando água",
        "excerpt": "Quando o interior perde sua ordem diante de Deus, a vida externa começa a revelar fragmentos da alma.",
    },
]


def read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_heading(line: str) -> bool:
    stripped = line.strip(" .:-")
    if len(stripped) < 3:
        return False
    if re.match(r"^\d+[\s:-]", stripped):
        return True
    letters = [c for c in stripped if c.isalpha()]
    if not letters:
        return False
    uppercase_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    return uppercase_ratio > 0.82 and len(stripped) < 90


def join_wrapped_lines(lines: list[str]) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []

    def flush() -> None:
        nonlocal current
        if current:
            blocks.append(" ".join(current).strip())
            current = []

    for raw in lines:
        line = raw.strip()
        if not line:
            flush()
            continue
        if is_heading(line):
            flush()
            blocks.append(line)
            continue
        if line.startswith(("-", "•", "→")):
            flush()
            blocks.append(line)
            continue
        current.append(line)
    flush()
    return blocks


def article_body_html(text: str, title: str) -> str:
    lines = text.splitlines()
    blocks = join_wrapped_lines(lines)
    if blocks and blocks[0].upper().startswith(title.upper()[:18]):
        blocks = blocks[1:]

    result: list[str] = []
    for block in blocks:
        safe = html.escape(block)
        if block.startswith(("“", '"')) and len(block) < 220:
            result.append(f'<blockquote>{safe}</blockquote>')
        elif block.startswith(("-", "•", "→")):
            result.append(f"<p class=\"article-list-line\">{safe}</p>")
        elif is_heading(block):
            result.append(f"<h2>{safe.title()}</h2>")
        else:
            result.append(f"<p>{safe}</p>")
    return "\n".join(result)


def page_shell(title: str, description: str, body: str, canonical: str, image: str | None = None, prefix: str = "") -> str:
    og_image = f"{DOMAIN}/images/articles/{image}" if image else f"{DOMAIN}/images/articles/depois-da-festa.png"
    return f"""<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{html.escape(title)}</title>
    <meta name="description" content="{html.escape(description)}" />
    <link rel="canonical" href="{canonical}" />
    <meta property="og:type" content="website" />
    <meta property="og:title" content="{html.escape(title)}" />
    <meta property="og:description" content="{html.escape(description)}" />
    <meta property="og:image" content="{og_image}" />
    <meta property="og:url" content="{canonical}" />
    <meta name="twitter:card" content="summary_large_image" />
    <link rel="alternate" type="application/rss+xml" title="Verbo Vivo" href="{prefix}feed.xml" />
    <link rel="stylesheet" href="{prefix}styles.css" />
  </head>
  <body>
    <header class="site-header">
      <a class="brand" href="{prefix}index.html">
        <span class="brand-mark">VV</span>
        <span>
          <strong>Verbo Vivo</strong>
          <small>verbovivo.blog</small>
        </span>
      </a>
      <nav aria-label="Navegação principal">
        <a href="{prefix}index.html#artigos">Artigos</a>
        <a href="{prefix}index.html#editorial">Editorial</a>
        <a href="{prefix}index.html#sobre">Sobre</a>
      </nav>
    </header>
    {body}
    <footer class="site-footer">
      <p><strong>Verbo Vivo</strong> publica reflexões cristãs, estudos bíblicos e textos para fortalecer a fé na vida cotidiana.</p>
      <a href="{prefix}feed.xml">RSS</a>
    </footer>
  </body>
</html>
"""


def article_card(article: dict, featured: bool = False, prefix: str = "") -> str:
    cls = "featured" if featured else "article-card"
    return f"""
      <article class="{cls}">
        <a href="{prefix}artigos/{article['slug']}.html">
          <img src="{prefix}images/articles/{article['image']}" alt="{html.escape(article['alt'])}" />
        </a>
        <div class="article-body">
          <p class="category">{html.escape(article['category'])}</p>
          <h3><a href="{prefix}artigos/{article['slug']}.html">{html.escape(article['title'])}</a></h3>
          <p>{html.escape(article['excerpt'])}</p>
        </div>
      </article>
"""


def build_index(articles: list[dict]) -> None:
    featured = articles[0]
    cards = "\n".join(article_card(article) for article in articles)
    body = f"""
    <main>
      <section class="hero">
        <div class="hero-copy">
          <p class="eyebrow">Palavra, fé e vida cristã</p>
          <h1>Reflexões humanas, preparadas com cuidado para alimentar a caminhada.</h1>
          <p>
            O Verbo Vivo nasce para publicar artigos escritos por pessoas reais,
            com apoio automatizado na organização editorial, imagens, metadados
            e preparação técnica para publicação.
          </p>
        </div>
        {article_card(featured, featured=True)}
      </section>

      <section class="section-intro" id="artigos">
        <p class="eyebrow">Primeiros artigos</p>
        <h2>Três textos iniciais para o lançamento</h2>
      </section>

      <section class="article-grid" aria-label="Lista de artigos">
        {cards}
      </section>

      <section class="editorial" id="editorial">
        <div>
          <p class="eyebrow">Linha editorial</p>
          <h2>O texto vem de fonte humana. A automação cuida da preparação.</h2>
        </div>
        <div class="principles">
          <p>Revisão de clareza, sem apagar a voz do autor.</p>
          <p>Imagem contextual respeitosa, sem cenas bíblicas sensacionalistas.</p>
          <p>SEO técnico com título, descrição, slug, tags e dados estruturados.</p>
        </div>
      </section>

      <section class="about" id="sobre">
        <p class="eyebrow">Sobre o projeto</p>
        <h2>Uma casa digital para Palavra, fé e vida cristã.</h2>
        <p>
          Este é o primeiro modelo publicável do Verbo Vivo. A estrutura já foi
          preparada para receber novos artigos, gerar páginas individuais,
          alimentar RSS, sitemap e futuras rotinas automáticas de publicação.
        </p>
      </section>
    </main>
"""
    output = page_shell(
        "Verbo Vivo | Reflexões cristãs",
        "Textos cristãos, estudos bíblicos e reflexões para fortalecer a fé na vida cotidiana.",
        body,
        f"{DOMAIN}/",
    )
    (SITE / "index.html").write_text(output, encoding="utf-8")


def build_article(article: dict) -> None:
    text = read_pdf(article["pdf"])
    body_html = article_body_html(text, article["title"])
    body = f"""
    <main>
      <article class="article-page">
        <header class="article-hero">
          <div>
            <p class="category">{html.escape(article['category'])}</p>
            <h1>{html.escape(article['title'])}</h1>
            <p class="article-excerpt">{html.escape(article['excerpt'])}</p>
            <p class="article-meta">Por {html.escape(article['author'])} · {article['date']}</p>
          </div>
          <img src="../images/articles/{article['image']}" alt="{html.escape(article['alt'])}" />
        </header>
        <div class="article-content">
          {body_html}
        </div>
      </article>
    </main>
"""
    output = page_shell(
        f"{article['title']} | Verbo Vivo",
        article["excerpt"],
        body,
        f"{DOMAIN}/artigos/{article['slug']}.html",
        article["image"],
        "../",
    )
    (ARTICLE_DIR / f"{article['slug']}.html").write_text(output, encoding="utf-8")


def build_css() -> None:
    css = """
:root {
  --ink: #17201b;
  --muted: #59645c;
  --paper: #fbfaf6;
  --cream: #efe6d4;
  --line: #d8d0bf;
  --sage: #4f7059;
  --gold: #a9792e;
  --white: #fffdf8;
  --shadow: 0 18px 50px rgba(23, 32, 27, 0.09);
}

* {
  box-sizing: border-box;
}

html {
  background: var(--paper);
  color: var(--ink);
  font-family: Arial, Helvetica, sans-serif;
  scroll-behavior: smooth;
}

body {
  margin: 0;
}

a {
  color: inherit;
  text-decoration: none;
}

img {
  display: block;
  max-width: 100%;
}

.site-header {
  align-items: center;
  background: rgba(251, 250, 246, 0.92);
  border-bottom: 1px solid var(--line);
  display: flex;
  gap: 24px;
  justify-content: space-between;
  padding: 18px clamp(18px, 4vw, 64px);
  position: sticky;
  top: 0;
  z-index: 5;
}

.brand {
  align-items: center;
  display: inline-flex;
  gap: 12px;
}

.brand-mark {
  align-items: center;
  background: var(--ink);
  border-radius: 50%;
  color: var(--paper);
  display: inline-flex;
  font-weight: 700;
  height: 42px;
  justify-content: center;
  width: 42px;
}

.brand strong,
.brand small {
  display: block;
}

.brand strong {
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.15rem;
}

.brand small {
  color: var(--muted);
  font-size: 0.78rem;
}

nav {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
}

nav a {
  color: var(--muted);
  font-size: 0.92rem;
  font-weight: 700;
}

main {
  overflow: hidden;
}

.hero {
  display: grid;
  gap: clamp(24px, 4vw, 48px);
  grid-template-columns: minmax(0, 0.9fr) minmax(320px, 1.1fr);
  padding: clamp(36px, 7vw, 88px) clamp(18px, 4vw, 64px) clamp(30px, 6vw, 72px);
}

.hero-copy {
  align-self: center;
  max-width: 650px;
}

.eyebrow,
.category {
  color: var(--sage);
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  margin: 0 0 12px;
  text-transform: uppercase;
}

h1,
h2,
h3 {
  font-family: Georgia, "Times New Roman", serif;
  letter-spacing: 0;
  margin: 0;
}

.hero h1 {
  font-size: clamp(2.25rem, 5vw, 5rem);
  line-height: 0.96;
  max-width: 820px;
}

.hero-copy p:last-child,
.about p,
.article-excerpt {
  color: var(--muted);
  font-size: 1.08rem;
  line-height: 1.7;
  max-width: 620px;
}

.featured,
.article-card {
  background: var(--white);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
}

.featured img {
  aspect-ratio: 16 / 10;
  object-fit: cover;
  width: 100%;
}

.article-body {
  padding: clamp(18px, 3vw, 30px);
}

.article-body h3 {
  font-size: clamp(1.35rem, 2.2vw, 2rem);
  line-height: 1.08;
}

.article-body p:last-child {
  color: var(--muted);
  line-height: 1.6;
}

.section-intro,
.about {
  padding: 0 clamp(18px, 4vw, 64px);
}

.section-intro h2,
.about h2,
.editorial h2 {
  font-size: clamp(1.8rem, 3vw, 3.4rem);
  line-height: 1.02;
  max-width: 850px;
}

.article-grid {
  display: grid;
  gap: 22px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  padding: 28px clamp(18px, 4vw, 64px) clamp(40px, 6vw, 84px);
}

.article-card img {
  aspect-ratio: 16 / 10;
  object-fit: cover;
  width: 100%;
}

.editorial {
  background: var(--cream);
  border-block: 1px solid var(--line);
  display: grid;
  gap: 28px;
  grid-template-columns: 1fr 1fr;
  padding: clamp(36px, 6vw, 70px) clamp(18px, 4vw, 64px);
}

.principles {
  display: grid;
  gap: 14px;
}

.principles p {
  background: rgba(255, 253, 248, 0.58);
  border-left: 4px solid var(--gold);
  color: var(--muted);
  line-height: 1.55;
  margin: 0;
  padding: 14px 16px;
}

.about {
  padding-bottom: clamp(48px, 7vw, 96px);
  padding-top: clamp(42px, 7vw, 90px);
}

.article-page {
  padding: clamp(28px, 5vw, 70px) clamp(18px, 4vw, 64px) clamp(48px, 7vw, 96px);
}

.article-hero {
  align-items: center;
  display: grid;
  gap: clamp(24px, 5vw, 58px);
  grid-template-columns: minmax(0, 0.9fr) minmax(320px, 1.1fr);
  margin-bottom: clamp(34px, 6vw, 76px);
}

.article-hero h1 {
  font-size: clamp(2.3rem, 5vw, 5.4rem);
  line-height: 0.95;
}

.article-meta {
  color: var(--gold);
  font-weight: 800;
  margin-top: 22px;
}

.article-hero img {
  aspect-ratio: 16 / 10;
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
  object-fit: cover;
  width: 100%;
}

.article-content {
  margin-inline: auto;
  max-width: 820px;
}

.article-content h2 {
  font-size: clamp(1.55rem, 2.4vw, 2.35rem);
  line-height: 1.12;
  margin: 2.2em 0 0.65em;
}

.article-content p,
.article-content blockquote {
  color: #2d3831;
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(1.06rem, 1.4vw, 1.2rem);
  line-height: 1.86;
  margin: 0 0 1.15em;
}

.article-content blockquote {
  border-left: 4px solid var(--gold);
  color: var(--muted);
  padding-left: 18px;
}

.article-list-line {
  color: var(--muted) !important;
  padding-left: 18px;
}

.site-footer {
  align-items: center;
  border-top: 1px solid var(--line);
  color: var(--muted);
  display: flex;
  gap: 20px;
  justify-content: space-between;
  padding: 28px clamp(18px, 4vw, 64px);
}

.site-footer p {
  margin: 0;
}

.site-footer a {
  color: var(--sage);
  font-weight: 800;
}

@media (max-width: 900px) {
  .hero,
  .article-hero,
  .editorial {
    grid-template-columns: 1fr;
  }

  .article-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 620px) {
  .site-header,
  .site-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  nav {
    gap: 12px;
  }
}
"""
    (SITE / "styles.css").write_text(css.strip() + "\n", encoding="utf-8")


def build_sitemap(articles: list[dict]) -> None:
    urls = [f"{DOMAIN}/"] + [f"{DOMAIN}/artigos/{article['slug']}.html" for article in articles]
    body = "\n".join(f"  <url><loc>{url}</loc></url>" for url in urls)
    sitemap = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n'
    (SITE / "sitemap.xml").write_text(sitemap, encoding="utf-8")


def build_feed(articles: list[dict]) -> None:
    items = []
    for article in articles:
        url = f"{DOMAIN}/artigos/{article['slug']}.html"
        items.append(
            f"""
    <item>
      <title>{html.escape(article['title'])}</title>
      <link>{url}</link>
      <guid>{url}</guid>
      <description>{html.escape(article['excerpt'])}</description>
      <pubDate>{date.fromisoformat(article['date']).strftime('%a, %d %b %Y 00:00:00 +0000')}</pubDate>
    </item>"""
        )
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Verbo Vivo</title>
    <link>{DOMAIN}/</link>
    <description>Reflexões cristãs para fortalecer a fé e iluminar a caminhada.</description>
{''.join(items)}
  </channel>
</rss>
"""
    (SITE / "feed.xml").write_text(feed, encoding="utf-8")


def build_misc() -> None:
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n", encoding="utf-8")
    (SITE / "CNAME").write_text("verbovivo.blog\n", encoding="utf-8")
    (SITE / "humans.txt").write_text("Verbo Vivo\nConteúdo humano, preparação editorial assistida.\n", encoding="utf-8")


def main() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)
    ARTICLE_DIR.mkdir(parents=True)
    IMAGE_OUT.mkdir(parents=True)
    for image in IMAGE_IN.glob("*.png"):
        shutil.copy2(image, IMAGE_OUT / image.name)

    build_css()
    build_index(ARTICLES)
    for article in ARTICLES:
        build_article(article)
    build_sitemap(ARTICLES)
    build_feed(ARTICLES)
    build_misc()
    print(SITE.resolve())


if __name__ == "__main__":
    main()
