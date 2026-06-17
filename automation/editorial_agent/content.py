from __future__ import annotations

import json
import re
import secrets
import unicodedata
from datetime import datetime, timezone
from html import escape
from urllib.parse import urlparse

from .models import ArticleDraft


DOMAIN = "https://verbovivo.blog"
DEFAULT_AUTHOR = "Pastor Antônio Lemos"
DEFAULT_AUTHOR_SOCIALS = {
    "instagram": "https://www.instagram.com/antoniolemosoficial/",
    "youtube": "https://www.youtube.com/@Lemos3",
    "facebook": "https://www.facebook.com/PastorAntonioLemos",
}
REFERENCE_HEADINGS = {
    "fontes",
    "fontes e dicionarios de referencia",
    "referencias",
    "referencias bibliograficas",
    "bibliografia",
}


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return value or secrets.token_hex(4)


def paragraphs_from_text(text: str) -> list[str]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    if len(blocks) == 1:
        blocks = [line.strip() for line in text.splitlines() if line.strip()]
    return blocks


DIRECT_METADATA_LABELS = {
    "tema",
    "texto-chave",
    "texto chave",
    "palavra-chave exegetica",
    "palavra chave exegetica",
}


def strip_markdown_wrapper(value: str) -> str:
    value = value.strip()
    while len(value) >= 2 and value[:1] == value[-1:] and value[0] in {"*", "_"}:
        value = value[1:-1].strip()
    return value.strip("*_").strip()


def direct_line_kind(value: str) -> str:
    clean = value.strip()
    plain = strip_markdown_wrapper(clean.lstrip("#> "))
    if not clean:
        return "blank"
    if re.match(r"^[-*+]\s+\S", clean):
        return "list"
    if clean.startswith(">"):
        return "quote"
    if clean.startswith("#") or re.match(r"^\*{0,2}\d+\.\s+", clean):
        return "heading"
    if looks_like_direct_heading(plain):
        return "heading"
    label_match = re.match(r"^\*{0,2}([^:*]{2,45}):\*{0,2}\s*(.*)$", clean)
    if label_match and normalized_heading(label_match.group(1)) in DIRECT_METADATA_LABELS:
        return "metadata"
    return "text"


def reflow_direct_submission(text: str) -> list[str]:
    """Recompose email/Markdown lines without losing real block boundaries."""
    source_lines = [line.strip() for line in text.splitlines()]
    blocks: list[str] = []
    current = ""
    current_kind = ""

    def flush() -> None:
        nonlocal current, current_kind
        if current:
            blocks.append(current.strip())
        current = ""
        current_kind = ""

    for line in source_lines:
        if not line:
            # A blank line is advisory only. HTML email often inserts one after
            # every visually wrapped line, so punctuation and block markers are
            # more reliable than whitespace here.
            continue
        kind = direct_line_kind(line)
        if kind in {"heading", "metadata", "quote", "list"}:
            flush()
            current = line
            current_kind = kind
            heading_is_wrapped = kind == "heading" and (
                (line.startswith("**") and not line.endswith("**"))
                or bool(re.search(r"\b(?:cap[ií]tulo|vers[ií]culo|de|da|do|das|dos|e|em|para)$", line, re.IGNORECASE))
            )
            if kind == "list" or (kind == "heading" and not heading_is_wrapped):
                flush()
            continue
        if current_kind in {"heading", "metadata", "quote"}:
            current = f"{current} {line}".strip()
            balanced_parentheses = current.count("(") <= current.count(")")
            closes_markdown = current_kind == "heading" and line.endswith("**")
            terminal_punctuation = bool(re.search(r"[.!?;\u201d\"](?:\*{1,2})?$", line))
            if closes_markdown or (balanced_parentheses and terminal_punctuation):
                flush()
            continue
        if not current:
            current = line
            current_kind = "text"
            continue
        current = f"{current} {line}".strip()
        if re.search(r"[.!?\u201d\"](?:\*{1,2})?$", line):
            flush()
    flush()
    return blocks


def normalize_direct_submission_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    kept_lines: list[str] = []
    discard_patterns = (
        r"^\[image:\s*.*?\]$",
        r"^!\[.*?\]\(.*?\)$",
        r"^texto(?:\s+mais\s+imagem)?\s+do\s+artigo\s+come[cç]a\s+aqui\.{0,3}$",
        r"^[-_]{3,}$",
        r"^(?:enviado|sent)\s+(?:do|from)\s+meu\b",
        r"^(?:de|from|para|to|assunto|subject|data|date):\s",
    )
    for line in text.splitlines():
        clean = line.strip()
        clean = re.sub(r"^corpo\s+do\s+e-?mail:\s*", "", clean, flags=re.IGNORECASE)
        if re.match(r"^assunto\s+do\s+e-?mail:\s*", clean, re.IGNORECASE):
            continue
        if any(re.match(pattern, clean, re.IGNORECASE) for pattern in discard_patterns):
            continue
        if clean:
            kept_lines.append(clean)
    return "\n".join(kept_lines).strip()


def normalized_heading(value: str) -> str:
    value = value.strip("*# ").rstrip(":")
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()


def split_direct_references(text: str) -> tuple[str, str]:
    main_lines: list[str] = []
    reference_lines: list[str] = []
    in_references = False
    for line in text.splitlines():
        if normalized_heading(line) in REFERENCE_HEADINGS:
            in_references = True
            continue
        (reference_lines if in_references else main_lines).append(line)
    return "\n".join(main_lines).strip(), "\n".join(reference_lines).strip()


def direct_references_html(text: str) -> str:
    if not text.strip():
        return ""
    items: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        clean = line.strip()
        if not clean:
            continue
        if clean.startswith("- "):
            if current:
                items.append(" ".join(current))
            current = [clean[2:].strip()]
        else:
            current.append(clean)
    if current:
        items.append(" ".join(current))
    if not items:
        items = [text.strip()]
    rendered = "".join(f"<li>{inline_direct_markup(item)}</li>" for item in items)
    return (
        '<aside class="article-references" aria-label="Referências para aprofundamento">'
        "<h2>Para aprofundar a leitura</h2>"
        "<p>Estas obras podem ajudar o leitor que deseja ampliar o estudo bíblico e teológico relacionado à reflexão.</p>"
        f"<ul>{rendered}</ul>"
        "</aside>"
    )


def inline_direct_markup(text: str) -> str:
    text = re.sub(r"\$\\alpha\s+\\gamma\s+\\omega\s+\\nu\$", "agōn", text)
    text = re.sub(
        r"\b([1-3]?\s?[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÀ-ÿ]+)\s+(\d{1,3}):(\d{1,3})(?:\s*-\s*(\d{1,3}))?",
        lambda match: (
            f"{match.group(1)}, capítulo {match.group(2)}, versículos {match.group(3)} a {match.group(4)}"
            if match.group(4)
            else f"{match.group(1)}, capítulo {match.group(2)}, versículo {match.group(3)}"
        ),
        text,
    )
    value = escape(text.strip())
    value = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"\*(.+?)\*", r"<em>\1</em>", value)
    return value


def direct_metadata(value: str) -> tuple[str, str] | None:
    match = re.match(r"^\*{0,2}([^:*]{2,45}):\*{0,2}\s*(.*)$", value.strip())
    if not match:
        return None
    label = normalized_heading(match.group(1))
    if label not in DIRECT_METADATA_LABELS:
        return None
    return label, strip_markdown_wrapper(match.group(2))


def looks_like_direct_heading(text: str) -> bool:
    clean = text.strip("*# ").strip()
    if not clean or len(clean) > 86 or re.search(r"[.!?;:]$", clean):
        return False
    words = clean.split()
    if not 2 <= len(words) <= 12:
        return False
    lowercase_connectors = {"a", "ao", "aos", "as", "como", "contra", "da", "das", "de", "do", "dos", "e", "em", "na", "nas", "no", "nos", "o", "os", "para", "pela", "pelos", "por", "sem"}
    significant_words = [word for word in words if word.lower() not in lowercase_connectors]
    return bool(significant_words) and all(word[0].isupper() or word[0].isdigit() for word in significant_words)


def direct_article_html(text: str, title: str) -> str:
    cleaned_text = normalize_direct_submission_text(text)
    article_text, reference_text = split_direct_references(cleaned_text)
    blocks = reflow_direct_submission(article_text)
    body: list[str] = []
    list_items: list[str] = []

    def flush_list() -> None:
        if list_items:
            body.append("<ul>" + "".join(f"<li>{item}</li>" for item in list_items) + "</ul>")
            list_items.clear()

    normalized_title = slugify(title)
    for block in blocks:
        clean = re.sub(r"\s*\n\s*", " ", block.strip())
        if not clean:
            continue
        metadata = direct_metadata(clean)
        if metadata:
            label, value = metadata
            if label == "tema":
                continue
            label_text = "Texto-chave" if label in {"texto-chave", "texto chave"} else "Palavra-chave exegética"
            body.append(f'<p class="article-keyline"><strong>{label_text}:</strong> {inline_direct_markup(value)}</p>')
            continue
        if re.match(r"^[-*+]\s+", clean):
            list_items.append(inline_direct_markup(re.sub(r"^[-*+]\s+", "", clean)))
            continue
        flush_list()
        heading = strip_markdown_wrapper(clean.lstrip("# "))
        if slugify(heading) == normalized_title or slugify(heading).startswith(normalized_title + "-"):
            continue
        if re.match(r"^\*{0,2}\d+\.\s+", clean):
            body.append(f"<h2>{inline_direct_markup(heading)}</h2>")
        elif clean.startswith("#"):
            body.append(f"<h2>{inline_direct_markup(heading)}</h2>")
        elif clean.startswith("**") and clean.endswith("**") and len(clean) < 140:
            body.append(f"<h2>{inline_direct_markup(heading)}</h2>")
        elif looks_like_direct_heading(heading):
            body.append(f"<h2>{inline_direct_markup(heading)}</h2>")
        elif clean.startswith(">"):
            body.append(f"<blockquote>{inline_direct_markup(clean.lstrip('> '))}</blockquote>")
        elif clean.startswith(("“", '"')) and ("—" in clean or re.search(r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ÿ]+\s+\d+:\d+", clean)):
            body.append(f"<blockquote>{inline_direct_markup(clean)}</blockquote>")
        else:
            body.append(f"<p>{inline_direct_markup(clean)}</p>")
    flush_list()
    references_html = direct_references_html(reference_text)
    if references_html:
        body.append(references_html)
    return "\n".join(body)


def validate_direct_article_html(value: str) -> None:
    plain = re.sub(r"<[^>]+>", " ", value)
    word_count = len(re.findall(r"\b[\wÀ-ÿ'-]+\b", plain))
    problems: list[str] = []
    if word_count < 40:
        problems.append("conteúdo insuficiente")
    if "**" in value or re.search(r"<p>\s*&gt;", value):
        problems.append("marcação editorial não convertida")
    if re.search(r"<h2>[^<]*(?:cap[ií]tulo|vers[ií]culo)\s*</h2>", value, re.IGNORECASE):
        problems.append("título quebrado no meio de uma referência bíblica")
    if problems:
        raise ValueError("Publicação direta bloqueada: " + "; ".join(problems))


def normalize_social_url(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    if value.startswith("@"):
        return value
    parsed = urlparse(value if "://" in value else f"https://{value}")
    return parsed.geturl() if parsed.netloc else value


def extract_submission_metadata(source_text: str) -> tuple[dict, str]:
    metadata = {"author": "", "guest_author": False, "socials": {}}
    body_lines: list[str] = []
    in_header = True
    saw_header_field = False
    for line in source_text.splitlines():
        clean = line.strip()
        if in_header and not clean:
            if saw_header_field:
                in_header = False
            continue
        if in_header and ":" in clean:
            key, value = clean.split(":", 1)
            key_norm = unicodedata.normalize("NFKD", key).encode("ascii", "ignore").decode("ascii").lower().strip()
            value = value.strip()
            if key_norm in {"autor convidado", "author guest", "guest author"}:
                saw_header_field = True
                metadata["author"] = value
                metadata["guest_author"] = bool(value)
                continue
            if key_norm in {"autor", "author", "nome", "nome do autor"}:
                saw_header_field = True
                continue
            if key_norm in {"instagram", "facebook", "youtube", "x", "twitter", "linkedin", "site", "website"}:
                saw_header_field = True
                if value:
                    metadata["socials"][key_norm] = normalize_social_url(value)
                continue
        body_lines.append(line)
    body = "\n".join(body_lines).strip() or source_text.strip()
    return metadata, body


def submission_author(metadata: dict) -> str:
    return metadata["author"] if metadata.get("guest_author") else DEFAULT_AUTHOR


def submission_socials(metadata: dict) -> dict[str, str]:
    if metadata.get("guest_author"):
        return metadata["socials"]
    return DEFAULT_AUTHOR_SOCIALS.copy()


def social_label(name: str) -> str:
    return {
        "instagram": "Instagram",
        "facebook": "Facebook",
        "youtube": "YouTube",
        "x": "X",
        "twitter": "X",
        "linkedin": "LinkedIn",
        "site": "Site",
        "website": "Site",
    }.get(name.lower(), name.title())


def social_icon(name: str) -> str:
    icons = {
        "instagram": '<svg class="social-icon social-icon--instagram" aria-hidden="true" viewBox="0 0 24 24"><path d="M7.8 2h8.4C19.4 2 22 4.6 22 7.8v8.4c0 3.2-2.6 5.8-5.8 5.8H7.8C4.6 22 2 19.4 2 16.2V7.8C2 4.6 4.6 2 7.8 2Zm-.2 2A3.6 3.6 0 0 0 4 7.6v8.8C4 18.39 5.61 20 7.6 20h8.8c1.99 0 3.6-1.61 3.6-3.6V7.6C20 5.61 18.39 4 16.4 4H7.6Zm9.65 1.5a1.25 1.25 0 1 1 0 2.5 1.25 1.25 0 0 1 0-2.5ZM12 7a5 5 0 1 1 0 10 5 5 0 0 1 0-10Zm0 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z"/></svg>',
        "facebook": '<svg class="social-icon social-icon--facebook" aria-hidden="true" viewBox="0 0 24 24"><path d="M13.45 23.69v-7.98h3.25l.67-3.67h-3.92v-1.3c0-1.94.76-2.68 2.73-2.68.61 0 1.1.02 1.39.05V4.79c-.54-.15-1.85-.3-2.61-.3-4.01 0-5.86 1.89-5.86 5.98v1.58H6.63v3.67H9.1v7.98h4.35Z"/></svg>',
        "youtube": '<svg class="social-icon social-icon--youtube" aria-hidden="true" viewBox="0 0 24 24"><path d="M23.5 6.19a3.02 3.02 0 0 0-2.12-2.14C19.5 3.55 12 3.55 12 3.55s-7.5 0-9.38.5A3.02 3.02 0 0 0 .5 6.19C0 8.08 0 12 0 12s0 3.92.5 5.81a3.02 3.02 0 0 0 2.12 2.14c1.88.5 9.38.5 9.38.5s7.5 0 9.38-.5a3.02 3.02 0 0 0 2.12-2.14C24 15.92 24 12 24 12s0-3.92-.5-5.81ZM9.55 15.57V8.43L15.82 12l-6.27 3.57Z"/></svg>',
        "x": '<svg class="social-icon social-icon--x" aria-hidden="true" viewBox="0 0 24 24"><path d="M18.9 1.15h3.68l-8.04 9.19L24 22.85h-7.41l-5.8-7.59-6.64 7.59H.47l8.6-9.83L0 1.15h7.59l5.24 6.93 6.07-6.93Zm-1.29 19.49h2.04L6.48 3.24H4.29l13.32 17.4Z"/></svg>',
        "twitter": '<svg class="social-icon social-icon--x" aria-hidden="true" viewBox="0 0 24 24"><path d="M18.9 1.15h3.68l-8.04 9.19L24 22.85h-7.41l-5.8-7.59-6.64 7.59H.47l8.6-9.83L0 1.15h7.59l5.24 6.93 6.07-6.93Zm-1.29 19.49h2.04L6.48 3.24H4.29l13.32 17.4Z"/></svg>',
        "linkedin": '<svg class="social-icon social-icon--linkedin" aria-hidden="true" viewBox="0 0 24 24"><path d="M20.45 20.45h-3.55v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28ZM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13Zm1.78 13.02H3.56V9h3.56v11.45ZM22.22 0H1.77C.79 0 0 .77 0 1.72v20.56C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.72V1.72C24 .77 23.2 0 22.22 0Z"/></svg>',
        "site": '<svg class="social-icon social-icon--site" aria-hidden="true" viewBox="0 0 24 24"><path d="M14 3h7v7h-2V6.41l-9.29 9.3-1.42-1.42 9.3-9.29H14V3ZM5 5h6v2H7v10h10v-4h2v6H5V5Z"/></svg>',
        "website": '<svg class="social-icon social-icon--site" aria-hidden="true" viewBox="0 0 24 24"><path d="M14 3h7v7h-2V6.41l-9.29 9.3-1.42-1.42 9.3-9.29H14V3ZM5 5h6v2H7v10h10v-4h2v6H5V5Z"/></svg>',
    }
    return icons.get(name.lower(), icons["site"])


def author_socials_html(socials: dict[str, str]) -> str:
    links = []
    for name, url in socials.items():
        if not url:
            continue
        href = url
        if url.startswith("@"):
            handle = url.lstrip("@")
            if name == "instagram":
                href = f"https://instagram.com/{handle}"
            elif name in {"x", "twitter"}:
                href = f"https://x.com/{handle}"
        label = social_label(name)
        links.append(
            f'<a href="{escape(href)}" target="_blank" rel="noopener" '
            f'aria-label="{escape(label)}" title="{escape(label)}">{social_icon(name)}</a>'
        )
    if not links:
        return ""
    return '<div class="author-socials" aria-label="Redes sociais do autor">' + "".join(links) + "</div>"


def listen_controls() -> str:
    return """
            <div class="listen-tools" aria-label="Narração do artigo">
              <button class="listen-button" type="button" data-listen-toggle aria-label="Ouvir artigo" title="Ouvir artigo">
                <svg aria-hidden="true" viewBox="0 0 24 24" width="22" height="22">
                  <path d="M4 9v6h4l5 4V5L8 9H4z" fill="currentColor"></path>
                  <path d="M16 9.5c1.1 1.4 1.1 3.6 0 5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path>
                  <path d="M18.8 7c2.3 2.8 2.3 7.2 0 10" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path>
                </svg>
              </button>
              <span data-listen-status>Clique para ouvir o artigo.</span>
            </div>
"""


def top_book_strip() -> str:
    return """
    <section class="top-book-strip" aria-label="Livro em destaque">
      <span>Livro gratuito do autor</span>
      <strong>Servir através da Intercessão</strong>
      <a href="https://www.editorakaleo.com/product-page/servir-atrav%C3%A9s-da-intercess%C3%A3o" target="_blank" rel="noopener">Acessar e-book</a>
    </section>
"""


RELATED_ARTICLES = [
    {
        "slug": "luta-invisivel",
        "title": "Luta Invisível",
        "excerpt": "A intercessão como serviço silencioso, amor pastoral e perseverança diante de Deus.",
    },
    {
        "slug": "tesouros-escondidos-em-cristo-a-sabedoria-que-transforma",
        "title": "Tesouros escondidos em Cristo",
        "excerpt": "A sabedoria que transforma nasce do conhecimento profundo de Cristo.",
    },
    {
        "slug": "palavras-que-enganam-vigilancia-e-discernimento-na-vida-crista",
        "title": "Palavras que Enganam",
        "excerpt": "Discernimento espiritual para reconhecer discursos sedutores e permanecer firme na verdade.",
    },
    {
        "slug": "o-coracao-desordenado-guardando-a-fonte-da-vida",
        "title": "O Coração Desordenado",
        "excerpt": "Uma reflexão sobre guardar a fonte da vida e ordenar o coração diante de Deus.",
    },
]


def related_articles_html(current_slug: str) -> str:
    items = [item for item in RELATED_ARTICLES if item["slug"] != current_slug][:3]
    if not items:
        return ""
    cards = "".join(
        (
            '<a class="related-card" href="../artigos/{slug}.html">'
            "<strong>{title}</strong>"
            "<span>{excerpt}</span>"
            "</a>"
        ).format(
            slug=escape(item["slug"]),
            title=escape(item["title"]),
            excerpt=escape(item["excerpt"]),
        )
        for item in items
    )
    return (
        '<aside class="related-reading" aria-label="Leia tambem">'
        "<p>Leia também</p>"
        "<h2>Continue a reflexão</h2>"
        f'<div class="related-grid">{cards}</div>'
        "</aside>"
    )


def seo_page_title(draft: ArticleDraft) -> str:
    value = (draft.seo_title or "").strip()
    if not value:
        value = draft.title.strip()
    if "verbo vivo" not in value.lower():
        value = f"{value} | Verbo Vivo"
    return value


def seo_page_description(draft: ArticleDraft) -> str:
    return (draft.seo_description or draft.excerpt or "Reflexão cristã para fortalecer a fé na vida cotidiana.").strip()


def parse_article_datetime(value: str) -> datetime:
    clean = (value or "").strip()
    if clean.endswith("Z"):
        clean = clean[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(clean)
    except ValueError:
        parsed = datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def article_publication_iso(draft: ArticleDraft) -> str:
    return parse_article_datetime(draft.created_at).isoformat()


def article_publication_label(draft: ArticleDraft) -> str:
    months = [
        "janeiro",
        "fevereiro",
        "março",
        "abril",
        "maio",
        "junho",
        "julho",
        "agosto",
        "setembro",
        "outubro",
        "novembro",
        "dezembro",
    ]
    published = parse_article_datetime(draft.created_at)
    return f"{published.day} de {months[published.month - 1]} de {published.year}"


def listen_script() -> str:
    return """
    <script>
      (() => {
        const controls = document.querySelector(".listen-tools");
        const article = document.querySelector(".article-content");
        if (!controls || !article) return;
        const status = controls.querySelector("[data-listen-status]");
        const button = controls.querySelector("[data-listen-toggle]");
        const synthesis = window.speechSynthesis;
        let utterance = null;
        const setStatus = (message) => { if (status) status.textContent = message; };
        const setButton = (speaking) => {
          if (!button) return;
          button.classList.toggle("is-speaking", speaking);
          button.setAttribute("aria-label", speaking ? "Pausar narração" : "Ouvir artigo");
          button.setAttribute("title", speaking ? "Pausar narração" : "Ouvir artigo");
        };
        if (!("speechSynthesis" in window)) {
          if (button) button.disabled = true;
          setStatus("Narração indisponível neste navegador.");
          return;
        }
        const expandBibleReferences = (text) => text.replace(
          /\\b([1-3]?\\s?[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç]+)\\s+(\\d{1,3}):(\\d{1,3})(?:-(\\d{1,3}))?/g,
          (_, book, chapter, verse, endVerse) => {
            const cleanBook = book.replace(/\\s+/g, " ").trim();
            return endVerse
              ? `${cleanBook}, capítulo ${chapter}, versículos ${verse} a ${endVerse}`
              : `${cleanBook}, capítulo ${chapter}, versículo ${verse}`;
          }
        );
        const articleText = () => expandBibleReferences(article.innerText).replace(/\\s+/g, " ").trim();
        const stop = () => {
          synthesis.cancel();
          utterance = null;
          setButton(false);
          setStatus("Narração parada.");
        };
        controls.addEventListener("click", (event) => {
          if (!event.target.closest("[data-listen-toggle]")) return;
          if (synthesis.speaking && !synthesis.paused) {
            synthesis.pause();
            setButton(false);
            setStatus("Narração pausada.");
            return;
          }
          if (synthesis.paused) {
            synthesis.resume();
            setButton(true);
            setStatus("Narrando artigo.");
            return;
          }
          stop();
          utterance = new SpeechSynthesisUtterance(articleText());
          utterance.lang = "pt-BR";
          utterance.rate = 0.95;
          utterance.onend = () => { setButton(false); setStatus("Narração concluída."); };
          utterance.onerror = () => { setButton(false); setStatus("Não foi possível narrar este artigo."); };
          synthesis.speak(utterance);
          setButton(true);
          setStatus("Narrando artigo.");
        });
        window.addEventListener("beforeunload", () => synthesis.cancel());
      })();
    </script>
"""


def analytics_head() -> str:
    return """
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-KRH6PSKSMV"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-KRH6PSKSMV');
    </script>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5233928852442075" crossorigin="anonymous"></script>
"""


def analytics_script(endpoint: str = "analytics.php") -> str:
    return f"""
    <script>
      (() => {{
        const endpoint = "{endpoint}";
        const now = Date.now();
        const sessionKey = "vv_session_id";
        const pageKey = "vv_page_id";
        let sessionId = sessionStorage.getItem(sessionKey);
        if (!sessionId) {{
          sessionId = crypto.randomUUID ? crypto.randomUUID() : `${{now}}-${{Math.random().toString(36).slice(2)}}`;
          sessionStorage.setItem(sessionKey, sessionId);
        }}
        const pageId = crypto.randomUUID ? crypto.randomUUID() : `${{now}}-${{Math.random().toString(36).slice(2)}}`;
        sessionStorage.setItem(pageKey, pageId);
        const payload = (eventName) => ({{
          event: eventName,
          session_id: sessionId,
          page_id: pageId,
          path: location.pathname,
          title: document.title,
          referrer: document.referrer || "",
          elapsed_seconds: Math.max(0, Math.round((Date.now() - now) / 1000)),
          language: navigator.language || "",
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "",
          screen: `${{screen.width}}x${{screen.height}}`,
          viewport: `${{innerWidth}}x${{innerHeight}}`
        }});
        const send = (eventName) => {{
          const body = JSON.stringify(payload(eventName));
          if (navigator.sendBeacon) {{
            navigator.sendBeacon(endpoint, new Blob([body], {{ type: "application/json" }}));
            return;
          }}
          fetch(endpoint, {{ method: "POST", headers: {{ "Content-Type": "application/json" }}, body, keepalive: true }}).catch(() => {{}});
        }};
        send("pageview");
        const timer = setInterval(() => send("heartbeat"), 15000);
        window.addEventListener("pagehide", () => {{
          clearInterval(timer);
          send("pagehide");
        }});
      }})();
    </script>
"""


def plain_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def trim_sentence(value: str, limit: int) -> str:
    value = plain_text(value)
    if len(value) <= limit:
        return value
    cut = value[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,.;:")
    return f"{cut}."


def seo_title_from_text(title: str, body: str = "") -> str:
    title = plain_text(title)
    body_lower = plain_text(body).lower()
    if "oração" in body_lower or "intercess" in body_lower:
        base = f"O que a Bíblia ensina sobre {title.lower()}"
    elif "coração" in body_lower:
        base = "Como guardar o coração segundo a Bíblia"
    elif "fé" in body_lower:
        base = f"{title}: reflexão bíblica para fortalecer a fé"
    else:
        base = title
    return trim_sentence(base, 58)


def seo_description_from_text(body: str) -> str:
    text = plain_text(body)
    if not text:
        return "Reflexão cristã para fortalecer a fé na vida cotidiana."
    return trim_sentence(text, 154)


def seo_keywords_from_title(title: str) -> str:
    title = plain_text(title).lower()
    title = re.sub(r"[^a-z0-9áéíóúâêôãõç\s-]", "", title)
    words = [word for word in title.split() if len(word) > 2]
    return " ".join(words[:6]) or "reflexão cristã"


def fallback_refine(source_text: str, subject: str, sender: str) -> ArticleDraft:
    metadata, article_text = extract_submission_metadata(source_text)
    blocks = paragraphs_from_text(article_text)
    title = subject.strip() or "Nova reflexão"
    selected = blocks[:8]
    body = ["<h2>Reflexão</h2>"]
    for paragraph in selected:
        body.append(f"<p>{escape(paragraph)}</p>")
    body.append("<h2>Para meditar</h2>")
    body.append("<p>Que esta palavra seja lida com calma, oração e abertura diante de Deus.</p>")
    slug = slugify(title)
    draft_id = secrets.token_hex(8)
    return ArticleDraft(
        id=draft_id,
        token=secrets.token_urlsafe(24),
        sender=sender,
        source_subject=subject,
        source_text=article_text,
        title=title,
        slug=slug,
        excerpt="Uma reflexão cristã preparada para leitura, meditação e fortalecimento da fé.",
        category="Reflexão",
        author=submission_author(metadata),
        body_html="\n".join(body),
        image_prompt=f"Imagem editorial cristã, reverente e simbólica para o tema: {title}",
        image_filename=f"{slug}-{draft_id}.png",
        author_socials=submission_socials(metadata),
        seo_title=seo_title_from_text(title, article_text),
        seo_description=seo_description_from_text(article_text),
        seo_keywords=seo_keywords_from_title(title),
    )


def render_article_page(draft: ArticleDraft) -> str:
    image_html = ""
    article_url = f"{DOMAIN}/artigos/{draft.slug}.html"
    image_url = ""
    page_title = seo_page_title(draft)
    page_description = seo_page_description(draft)
    if draft.image_filename:
        image_html = f'<img src="../images/articles/{escape(draft.image_filename)}" alt="{escape(draft.title)}" />'
        image_url = f"{DOMAIN}/images/articles/{draft.image_filename}"
    schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "mainEntityOfPage": {"@type": "WebPage", "@id": article_url},
        "headline": draft.title,
        "description": page_description,
        "image": [image_url] if image_url else [],
        "datePublished": article_publication_iso(draft),
        "dateModified": article_publication_iso(draft),
        "author": {"@type": "Person", "name": draft.author, "url": f"{DOMAIN}/autor.html"},
        "publisher": {"@type": "Organization", "name": "Verbo Vivo", "url": DOMAIN},
        "inLanguage": "pt-BR",
        "articleSection": draft.category,
    }
    if draft.seo_keywords:
        schema["keywords"] = draft.seo_keywords
    schema_json = json.dumps(schema, ensure_ascii=False, indent=2)
    return f"""<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{escape(page_title)}</title>
    <meta name="description" content="{escape(page_description)}" />
    <link rel="canonical" href="{escape(article_url)}" />
    <meta property="og:type" content="article" />
    <meta property="og:title" content="{escape(draft.title)}" />
    <meta property="og:description" content="{escape(page_description)}" />
    <meta property="og:url" content="{escape(article_url)}" />
    {f'<meta property="og:image" content="{escape(image_url)}" />' if image_url else ''}
    <meta name="twitter:card" content="summary_large_image" />
    <link rel="stylesheet" href="../styles.css?v=20260617-publication-date" />
    <script type="application/ld+json">
{schema_json}
    </script>
    {analytics_head()}
  </head>
  <body>
    <header class="site-header">
      <a class="brand" href="../index.html">
        <span class="brand-mark">VV</span>
        <span><strong>Verbo Vivo</strong><small>verbovivo.blog</small></span>
      </a>
      <nav aria-label="Navegação principal">
        <a href="../index.html#artigos">Artigos</a>
        <a href="../autor.html">Autor</a>
        <a href="../sobre.html">Sobre</a>
        <a href="../contato.html">Contato</a>
        <a href="../faq.html">FAQ</a>
      </nav>
    </header>
    {top_book_strip()}
    <main>
      <article class="article-page">
        <header class="article-hero">
          <div>
            <p class="category">{escape(draft.category)}</p>
            <h1>{escape(draft.title)}</h1>
            <p class="article-excerpt">{escape(draft.excerpt)}</p>
            <p class="article-meta">Por {escape(draft.author)}</p>
            {author_socials_html(draft.author_socials)}
            {listen_controls()}
          </div>
          {image_html}
        </header>
        <div class="article-content">
          {draft.body_html}
        </div>
        <p class="publication-date">Publicado em <time datetime="{escape(article_publication_iso(draft))}">{escape(article_publication_label(draft))}</time>.</p>
        {related_articles_html(draft.slug)}
      </article>
    </main>
    <footer class="site-footer">
      <p><strong>Verbo Vivo</strong> publica reflexões cristãs para fortalecer a fé na vida cotidiana.</p>
      <div><a href="../autor.html">Autor</a><a href="../sobre.html">Sobre</a><a href="../contato.html">Contato</a><a href="../faq.html">FAQ</a><a href="https://instagram.com/tec.agora" target="_blank" rel="noopener">By @tec.agora</a></div>
    </footer>
    {listen_script()}
    {analytics_script("../analytics.php")}
  </body>
</html>
"""


def ready_article_from_email(subject: str, source_text: str, sender: str, image_filename: str = "", image_path: str = "") -> ArticleDraft:
    metadata, article_text = extract_submission_metadata(source_text)
    article_text = normalize_direct_submission_text(article_text)
    blocks = reflow_direct_submission(article_text)
    title = subject.strip() or (blocks[0][:80] if blocks else "Nova reflexão")
    slug = slugify(title)
    description_source = " ".join(
        block for block in blocks
        if direct_line_kind(block) == "text" and not direct_metadata(block)
    )
    body_html = direct_article_html(article_text, title)
    validate_direct_article_html(body_html)
    return ArticleDraft(
        id=secrets.token_hex(8),
        token=secrets.token_urlsafe(24),
        sender=sender,
        source_subject=subject,
        source_text=article_text,
        title=title,
        slug=slug,
        excerpt="Uma reflexão cristã para fortalecer a fé na vida cotidiana.",
        category="Reflexão",
        author=submission_author(metadata),
        body_html=body_html,
        image_prompt="",
        image_filename=image_filename,
        author_socials=submission_socials(metadata),
        local_image_path=image_path,
        seo_title=seo_title_from_text(title, description_source),
        seo_description=seo_description_from_text(description_source),
        seo_keywords=seo_keywords_from_title(title),
        status="published_direct",
    )
