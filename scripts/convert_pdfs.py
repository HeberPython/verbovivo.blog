from pathlib import Path

from pypdf import PdfReader


SOURCE_DIR = Path(r"C:\Users\Heber\Documents\verbovivo.blog")
OUT_DIR = Path(__file__).resolve().parents[1] / "content" / "articles"

ARTICLES = [
    {
        "pdf": "DEPOIS DA FESTA.pdf",
        "file": "depois-da-festa-onde-ficou-jesus.md",
        "title": "Depois da Festa: onde ficou Jesus?",
        "slug": "depois-da-festa-onde-ficou-jesus",
        "category": "Vida Cristã",
        "cover": "/images/articles/depois-da-festa.png",
        "alt": "Rua antiga vazia ao anoitecer com ramos no chão e uma casa iluminada ao fundo",
    },
    {
        "pdf": "FILIPENSES - FEITOS PARA BRILHAR - Palestra - Heber.pdf",
        "file": "feitos-para-brilhar-pela-palavra-da-vida.md",
        "title": "Feitos para brilhar pela Palavra da Vida",
        "slug": "feitos-para-brilhar-pela-palavra-da-vida",
        "category": "Estudo Bíblico",
        "cover": "/images/articles/feitos-para-brilhar.png",
        "alt": "Bíblia aberta sobre mesa sob céu estrelado antes do amanhecer",
    },
    {
        "pdf": "LIÇÃO - CORAÇÃO DESORDENADO.pdf",
        "file": "o-coracao-desordenado.md",
        "title": "O coração desordenado",
        "slug": "o-coracao-desordenado",
        "category": "Formação Interior",
        "cover": "/images/articles/coracao-desordenado.png",
        "alt": "Mesa de estudo com Bíblia aberta, papéis e vaso de barro rachado derramando água",
    },
]


def extract_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    pages = []
    for page in reader.pages:
        text = (page.extract_text() or "").strip()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


def frontmatter(article: dict, source: Path) -> str:
    return "\n".join(
        [
            "---",
            f'title: "{article["title"]}"',
            f'slug: "{article["slug"]}"',
            'date: "2026-05-10"',
            'author: "Heber"',
            f'category: "{article["category"]}"',
            'status: "draft"',
            f'coverImage: "{article["cover"]}"',
            f'imageAlt: "{article["alt"]}"',
            f'sourcePdf: "{str(source).replace("\\", "\\\\")}"',
            "---",
            "",
        ]
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for article in ARTICLES:
        source = SOURCE_DIR / article["pdf"]
        text = extract_text(source)
        output = OUT_DIR / article["file"]
        output.write_text(frontmatter(article, source) + text + "\n", encoding="utf-8")
        print(f"Wrote {output}")


if __name__ == "__main__":
    main()
