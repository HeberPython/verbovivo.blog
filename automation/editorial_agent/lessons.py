from __future__ import annotations

import base64
import json
import mimetypes
import re
import secrets
import unicodedata
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from ftplib import FTP
from html import escape
from io import BytesIO
from pathlib import Path

from .config import settings
from .content import slugify
from .publisher import DOMAIN, SITE_DIR, ensure_dir, http_upload, remote_text, sitemap_entry


LESSON_PRODUCT_URL = "https://www.editorakaleo.com/product-page/revista-escola-b%C3%ADblica-jesus-aluno"
KALEO_SHOP_URL = "https://www.editorakaleo.com/shop"
LESSON_DIR = SITE_DIR / "licoes"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".heic", ".heif"}


@dataclass
class DailyReading:
    day: str
    summary: str
    reference: str = ""


@dataclass
class LessonSubtopic:
    heading: str
    summary: str


@dataclass
class LessonTopic:
    heading: str
    summary: str = ""
    subtopics: list[LessonSubtopic] = field(default_factory=list)


@dataclass
class LessonSummary:
    number: int
    title: str
    series: str = ""
    month_or_period: str = ""
    lesson_author: str = ""
    key_text: str = ""
    daily_wisdom: list[DailyReading] = field(default_factory=list)
    bible_reading: str = ""
    introduction: str = ""
    topics: list[LessonTopic] = field(default_factory=list)
    applications: list[str] = field(default_factory=list)
    conclusion: str = ""
    weekly_reflection: str = ""
    references: list[str] = field(default_factory=list)
    published_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def slug(self) -> str:
        return slugify(f"licao-{self.number}-{self.title}")


def strip_accents(value: str) -> str:
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")


def lesson_number_from_subject(subject: str) -> int | None:
    normalized = strip_accents(subject or "").lower()
    match = re.search(r"\b(?:licao|licoes)\s*0?([1-9]|1[0-3])\b", normalized)
    if not match:
        return None
    return int(match.group(1))


def is_lesson_subject(subject: str) -> bool:
    return lesson_number_from_subject(subject) is not None


def image_attachments(message) -> list:
    attachments = []
    for attachment in getattr(message, "attachments", []) or []:
        filename = (getattr(attachment, "filename", "") or "").lower()
        suffix = Path(filename).suffix.lower()
        content_type = (getattr(attachment, "content_type", "") or "").lower()
        if suffix in IMAGE_EXTENSIONS or content_type.startswith("image/"):
            attachments.append(attachment)
    return attachments


def lesson_prompt(number: int, subject: str) -> str:
    return f"""
Você é o editor do Verbo Vivo para a página "Lições Escola Dominical".
Receberá fotos de uma lição de Escola Bíblica Dominical já estudada em classe.

Tarefa:
- Extraia das imagens o número da lição, título, série, mês/período, autor quando aparecer, texto-chave, sabedoria diária, leitura bíblica, títulos e subtítulos.
- Publique como compêndio/resumo retrospectivo do que foi estudado, nunca como preparação para uma lição futura.
- Preserve sem alterar textos bíblicos, sugestões de leitura bíblica, texto-chave, referências bíblicas e perguntas da reflexão.
- Para conteúdo autoral da revista, não transcreva integralmente: faça resumo por tópico, mantendo a ordem e os títulos originais.
- Use português do Brasil, tom claro, reverente e didático.
- Escreva referências bíblicas por extenso: "Mateus, capítulo 7, versículo 29", nunca "Mt 7.29" ou "7:29".
- Credite o autor da lição quando ele aparecer nas imagens. Se não aparecer, deixe vazio.
- Não mencione agente, OCR, IA, e-mail, imagens recebidas nem instruções internas.

Assunto do e-mail: {subject}
Número esperado pelo assunto: Lição {number:02d}

Responda somente JSON válido, sem markdown, com este formato:
{{
  "number": {number},
  "title": "Título da lição",
  "series": "Série ou trimestre, se aparecer",
  "month_or_period": "Mês ou período, se aparecer",
  "lesson_author": "Autor da lição, se aparecer",
  "key_text": "Texto-chave preservado com referência bíblica por extenso",
  "daily_wisdom": [
    {{"day": "Segunda-feira", "summary": "Síntese preservada", "reference": "Referência por extenso"}}
  ],
  "bible_reading": "Leitura bíblica preservada com referências por extenso",
  "introduction": "Resumo da introdução",
  "topics": [
    {{
      "heading": "Título original do tópico",
      "summary": "Síntese do tópico se houver texto antes dos subtópicos",
      "subtopics": [
        {{"heading": "Subtítulo original", "summary": "Síntese fiel, sem transcrição integral"}}
      ]
    }}
  ],
  "applications": ["Aplicando o texto preservado ou resumido com fidelidade"],
  "conclusion": "Resumo da conclusão",
  "weekly_reflection": "Pergunta/reflexão da semana preservada",
  "references": ["Referências bibliográficas que aparecerem no rodapé ou no texto"]
}}
""".strip()


def gemini_json_from_images(message, number: int) -> dict:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY não está configurada para OCR das lições.")

    attachments = image_attachments(message)
    if not attachments:
        raise RuntimeError("Nenhuma imagem anexada foi encontrada para a lição.")

    parts: list[dict] = [{"text": lesson_prompt(number, message.subject or f"Lição {number:02d}")}]
    for attachment in attachments[:16]:
        filename = getattr(attachment, "filename", "") or ""
        content_type = getattr(attachment, "content_type", "") or ""
        mime_type = content_type or mimetypes.guess_type(filename)[0] or "image/jpeg"
        parts.append(
            {
                "inlineData": {
                    "mimeType": mime_type,
                    "data": base64.b64encode(attachment.payload).decode("ascii"),
                }
            }
        )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_text_model}:generateContent"
    payload = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": settings.gemini_api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini OCR falhou ({exc.code}): {detail[:500]}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Gemini OCR falhou: {exc.__class__.__name__}") from exc

    text = first_text_part(data)
    if not text:
        raise RuntimeError("Gemini OCR não retornou texto estruturado.")
    return json.loads(clean_json_text(text))


def first_text_part(data: dict) -> str:
    for candidate in data.get("candidates", []):
        content = candidate.get("content") or {}
        for part in content.get("parts", []):
            if part.get("text"):
                return str(part["text"])
    return ""


def clean_json_text(value: str) -> str:
    value = value.strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*", "", value)
        value = re.sub(r"\s*```$", "", value)
    return value.strip()


def as_text(value) -> str:
    return " ".join(str(value or "").split())


def list_of_strings(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [as_text(item) for item in value if as_text(item)]


def lesson_from_data(data: dict, fallback_number: int) -> LessonSummary:
    number = int(data.get("number") or fallback_number)
    title = as_text(data.get("title")) or f"Lição {number:02d}"
    daily: list[DailyReading] = []
    for item in data.get("daily_wisdom") or []:
        if not isinstance(item, dict):
            continue
        day = as_text(item.get("day"))
        summary = as_text(item.get("summary"))
        reference = as_text(item.get("reference"))
        if day or summary or reference:
            daily.append(DailyReading(day=day, summary=summary, reference=reference))

    topics: list[LessonTopic] = []
    for item in data.get("topics") or []:
        if not isinstance(item, dict):
            continue
        subtopics = [
            LessonSubtopic(heading=as_text(sub.get("heading")), summary=as_text(sub.get("summary")))
            for sub in item.get("subtopics") or []
            if isinstance(sub, dict) and (as_text(sub.get("heading")) or as_text(sub.get("summary")))
        ]
        heading = as_text(item.get("heading"))
        summary = as_text(item.get("summary"))
        if heading or summary or subtopics:
            topics.append(LessonTopic(heading=heading, summary=summary, subtopics=subtopics))

    return LessonSummary(
        number=number,
        title=title,
        series=as_text(data.get("series")),
        month_or_period=as_text(data.get("month_or_period")),
        lesson_author=as_text(data.get("lesson_author")),
        key_text=as_text(data.get("key_text")),
        daily_wisdom=daily,
        bible_reading=as_text(data.get("bible_reading")),
        introduction=as_text(data.get("introduction")),
        topics=topics,
        applications=list_of_strings(data.get("applications")),
        conclusion=as_text(data.get("conclusion")),
        weekly_reflection=as_text(data.get("weekly_reflection")),
        references=list_of_strings(data.get("references")),
    )


def pt_br_date(value: datetime) -> str:
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
    local = value.astimezone(timezone.utc)
    return f"{local.day} de {months[local.month - 1]} de {local.year}"


def paragraph(value: str) -> str:
    return f"<p>{escape(value)}</p>" if value else ""


def render_lesson_page(lesson: LessonSummary) -> str:
    page_url = f"{DOMAIN}/licoes/{lesson.slug}.html"
    description = (
        f"Compêndio retrospectivo da Lição {lesson.number}, {lesson.title}, "
        "com texto-chave, sabedoria diária, leitura bíblica e síntese por tópicos."
    )
    series_line = lesson.series or "Escola Bíblica Dominical"
    author_line = (
        f"<p><strong>Autor da lição:</strong> {escape(lesson.lesson_author)}.</p>"
        if lesson.lesson_author
        else ""
    )
    period_line = f"<p><strong>Período:</strong> {escape(lesson.month_or_period)}.</p>" if lesson.month_or_period else ""
    daily_html = ""
    if lesson.daily_wisdom:
        daily_html = "<h2>Sabedoria diária</h2><ul class=\"lesson-daily-list\">"
        for item in lesson.daily_wisdom:
            detail = " ".join(part for part in [item.summary, item.reference] if part)
            daily_html += f"<li><strong>{escape(item.day or 'Leitura')}:</strong> {escape(detail)}</li>"
        daily_html += "</ul>"

    topics_html = ""
    if lesson.introduction:
        topics_html += f"""
            <section class="lesson-topic">
              <h2>Introdução</h2>
              {paragraph(lesson.introduction)}
            </section>
"""
    for topic in lesson.topics:
        subtopics = ""
        for subtopic in topic.subtopics:
            subtopics += f"""
              <article>
                <h3>{escape(subtopic.heading)}</h3>
                {paragraph(subtopic.summary)}
              </article>
"""
        topics_html += f"""
            <section class="lesson-topic">
              <h2>{escape(topic.heading)}</h2>
              {paragraph(topic.summary)}
              {subtopics}
            </section>
"""
    for application in lesson.applications:
        topics_html += f"""
            <section class="lesson-application">
              <h2>Aplicando o texto</h2>
              {paragraph(application)}
            </section>
"""
    if lesson.conclusion:
        topics_html += f"""
            <section class="lesson-topic">
              <h2>Conclusão</h2>
              {paragraph(lesson.conclusion)}
            </section>
"""
    if lesson.weekly_reflection:
        topics_html += f"""
            <section class="lesson-reflection">
              <h2>Reflexão da semana</h2>
              {paragraph(lesson.weekly_reflection)}
            </section>
"""

    references = lesson.references + [
        f"Compêndio retrospectivo baseado na Lição {lesson.number}, {lesson.title}, {series_line}. Editora Kaleo.",
    ]
    references_html = "".join(f"<li>{escape(item)}</li>" for item in references if item)

    published_iso = lesson.published_at.date().isoformat()
    published_human = pt_br_date(lesson.published_at)
    return f"""<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Lição {lesson.number}: {escape(lesson.title)} | Lições Escola Dominical</title>
    <meta name="description" content="{escape(description)}" />
    <link rel="canonical" href="{page_url}" />
    <meta property="og:type" content="article" />
    <meta property="og:title" content="Lição {lesson.number}: {escape(lesson.title)} | Verbo Vivo" />
    <meta property="og:description" content="{escape(description)}" />
    <meta property="og:image" content="https://verbovivo.blog/images/articles/edificados-em-cristo.jpg" />
    <meta property="og:url" content="{page_url}" />
    <meta name="twitter:card" content="summary_large_image" />
    <link rel="stylesheet" href="../styles.css?v=20260824-lessons" />
    <script type="application/ld+json">
      {{
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "Lição {lesson.number}: {escape(lesson.title)}",
        "description": "{escape(description)}",
        "datePublished": "{published_iso}T00:00:00-03:00",
        "dateModified": "{published_iso}T00:00:00-03:00",
        "author": {{
          "@type": "Person",
          "name": "{escape(lesson.lesson_author or 'Verbo Vivo')}"
        }},
        "publisher": {{
          "@type": "Organization",
          "name": "Verbo Vivo",
          "url": "https://verbovivo.blog/"
        }},
        "mainEntityOfPage": "{page_url}",
        "articleSection": "Lições Escola Dominical",
        "inLanguage": "pt-BR"
      }}
    </script>
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-KRH6PSKSMV"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag("js", new Date());
      gtag("config", "G-KRH6PSKSMV");
    </script>
    <script async crossorigin="anonymous" src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5233928852442075"></script>
  </head>
  <body>
    <header class="site-header">
      <a class="brand" href="../index.html"><span class="brand-mark">VV</span><span><strong>Verbo Vivo</strong><small>verbovivo.blog</small></span></a>
      <nav aria-label="Navegação principal">
        <a href="../index.html#artigos">Artigos</a>
        <a href="../licoes-escola-dominical.html">Lições</a>
        <a href="../autor.html">Autor</a>
        <a href="../sobre.html">Sobre</a>
        <a href="../contato.html">Contato</a>
        <a href="../faq.html">FAQ</a>
        <a href="../politica-de-privacidade.html">Privacidade</a>
      </nav>
    </header>

    <section class="top-book-strip" aria-label="Livro em destaque">
      <span>Livro gratuito do autor</span>
      <strong>Servir através da Intercessão</strong>
      <a href="https://www.editorakaleo.com/product-page/servir-atrav%C3%A9s-da-intercess%C3%A3o" target="_blank" rel="noopener">Acessar e-book</a>
    </section>

    <main>
      <article class="article-page lesson-article">
        <header class="lesson-hero">
          <div>
            <p class="category">Lições Escola Dominical</p>
            <h1>Lição {lesson.number}: {escape(lesson.title)}</h1>
            <p class="article-excerpt">Compêndio retrospectivo da lição já estudada na Escola Bíblica Dominical, preservando a ordem dos tópicos, leituras bíblicas e perguntas principais, com síntese do conteúdo trabalhado em classe.</p>
            <p class="article-meta">Publicado em <time datetime="{published_iso}">{published_human}</time>.</p>
          </div>
          <aside class="lesson-cover-card" aria-label="Dados da lição">
            <span>Lição {lesson.number}</span>
            <strong>{escape(lesson.title)}</strong>
            <p>Série: {escape(series_line)}</p>
          </aside>
        </header>

        <section class="lesson-source-note" aria-label="Origem do resumo">
          <p>Compêndio retrospectivo baseado na Lição {lesson.number}, <strong>{escape(lesson.title)}</strong>, da série <strong>{escape(series_line)}</strong>. O material completo está disponível para aquisição no site da <a href="{LESSON_PRODUCT_URL}" target="_blank" rel="noopener">Editora Kaleo</a>.</p>
          {author_line}
          {period_line}
        </section>

        <section class="lesson-publisher-callout" aria-label="Editora Kaleo">
          <div>
            <p class="eyebrow">Editora Kaleo</p>
            <h2>Estude com o material oficial</h2>
            <p>Este compêndio não substitui a revista. Para acompanhar a lição completa, adquirir o material do trimestre e contribuir com a produção dos estudos, acesse a página oficial da Editora Kaleo.</p>
          </div>
          <div class="lesson-actions">
            <a href="{LESSON_PRODUCT_URL}" target="_blank" rel="noopener">Comprar esta revista</a>
            <a href="{KALEO_SHOP_URL}" target="_blank" rel="noopener">Ver loja da editora</a>
          </div>
        </section>

        <div class="article-content lesson-content">
          <section class="lesson-key-box">
            <h2>Texto-chave</h2>
            {paragraph(lesson.key_text)}
          </section>

          {daily_html}

          <h2>Leitura bíblica</h2>
          {paragraph(lesson.bible_reading)}

          <div class="lesson-outline">
            {topics_html}
          </div>

          <section class="article-references" aria-label="Referências e material oficial">
            <h2>Referências e aprofundamento</h2>
            <ul>
              {references_html}
              <li><a href="{LESSON_PRODUCT_URL}" target="_blank" rel="noopener">Página oficial desta revista na Editora Kaleo</a>.</li>
              <li><a href="{KALEO_SHOP_URL}" target="_blank" rel="noopener">Loja da Editora Kaleo com outras lições e materiais</a>.</li>
            </ul>
          </section>
        </div>
      </article>
    </main>

    <footer class="site-footer">
      <p><strong>Verbo Vivo</strong> publica reflexões cristãs para fortalecer a fé na vida cotidiana.</p>
      <div>
        <a href="../licoes-escola-dominical.html">Lições</a>
        <a href="../autor.html">Autor</a>
        <a href="../sobre.html">Sobre</a>
        <a href="../contato.html">Contato</a>
        <a href="../faq.html">FAQ</a>
        <a href="../politica-de-privacidade.html">Privacidade</a>
        <a href="../feed.xml">RSS</a>
        <a href="https://instagram.com/tec.agora" target="_blank" rel="noopener">By @tec.agora</a>
      </div>
    </footer>
  </body>
</html>
"""


def lesson_card(lesson: LessonSummary) -> str:
    series = f" · {lesson.series}" if lesson.series else ""
    excerpt = (
        f"Compêndio retrospectivo da Lição {lesson.number}, com texto-chave, leitura bíblica e síntese por tópicos do estudo realizado."
    )
    return f"""
          <article class="lesson-card" data-lesson-number="{lesson.number}">
            <div>
              <p class="category">Lição {lesson.number}{escape(series)}</p>
              <h2><a href="licoes/{escape(lesson.slug)}.html">{escape(lesson.title)}</a></h2>
              <p>{escape(excerpt)}</p>
            </div>
            <a class="lesson-card-link" href="licoes/{escape(lesson.slug)}.html">Abrir compêndio</a>
          </article>
"""


def merge_lesson_card(index_html: str, card_html: str, number: int) -> str:
    index_html = re.sub(
        rf'\s*<article class="lesson-card" data-lesson-number="{number}".*?</article>',
        "",
        index_html,
        flags=re.DOTALL,
    )
    index_html = re.sub(
        rf'\s*<article class="lesson-card">(?=.*?Lição {number}\b).*?</article>',
        "",
        index_html,
        flags=re.DOTALL,
    )
    match = re.search(r'(<section class="lesson-list"[^>]*>)(.*?)(\s*</section>)', index_html, flags=re.DOTALL)
    if not match:
        return index_html
    existing = match.group(2).strip()
    cards = re.findall(r'<article class="lesson-card".*?</article>', existing, flags=re.DOTALL)
    cards.append(card_html.strip())

    def card_number(card: str) -> int:
        data_match = re.search(r'data-lesson-number="(\d+)"', card)
        if data_match:
            return int(data_match.group(1))
        title_match = re.search(r"Lição\s+(\d+)", card)
        return int(title_match.group(1)) if title_match else 999

    ordered = sorted(cards, key=card_number)
    new_body = "\n".join("          " + card.strip() for card in ordered)
    return index_html[: match.start(2)] + "\n" + new_body + "\n        " + index_html[match.end(2) :]


def update_lesson_index(lesson: LessonSummary) -> Path:
    index_path = SITE_DIR / "licoes-escola-dominical.html"
    try:
        index_html = remote_text("licoes-escola-dominical.html")
    except RuntimeError:
        index_html = index_path.read_text(encoding="utf-8")
    index_html = index_html.replace("Guias autorais de estudo", "Compêndios e resumos retrospectivos")
    index_html = index_html.replace("Acompanhe guias de estudo", "Acompanhe compêndios e resumos retrospectivos")
    index_html = index_html.replace(
        "Esta área reúne resumos por tópicos para apoio à Escola Dominical.",
        "Esta área reúne resumos retrospectivos por tópicos das lições já estudadas na Escola Bíblica Dominical.",
    )
    index_html = index_html.replace("Abrir guia", "Abrir compêndio")
    index_html = merge_lesson_card(index_html, lesson_card(lesson), lesson.number)
    index_path.write_text(index_html, encoding="utf-8")
    return index_path


def update_lesson_sitemap(lesson: LessonSummary) -> Path:
    sitemap_path = SITE_DIR / "sitemap.xml"
    try:
        sitemap_xml = remote_text("sitemap.xml")
    except RuntimeError:
        sitemap_xml = sitemap_path.read_text(encoding="utf-8")
    url = f"{DOMAIN}/licoes/{lesson.slug}.html"
    if url not in sitemap_xml:
        sitemap_xml = sitemap_xml.replace("</urlset>", sitemap_entry(url) + "</urlset>", 1)
    sitemap_path.write_text(sitemap_xml, encoding="utf-8")
    return sitemap_path


def upload_lesson_files(paths: list[Path]) -> None:
    if settings.editorial_upload_url:
        for path in paths:
            http_upload(path.relative_to(SITE_DIR).as_posix(), path.read_bytes())
        return

    with FTP() as ftp:
        ftp.connect(settings.ftp_host, settings.ftp_port, timeout=60)
        ftp.login(settings.ftp_user, settings.ftp_password)
        ftp.set_pasv(True)
        ftp.cwd(settings.ftp_dir)
        for path in paths:
            remote_path = path.relative_to(SITE_DIR).as_posix()
            ensure_dir(ftp, str(Path(remote_path).parent))
            ftp.storbinary(f"STOR {remote_path}", BytesIO(path.read_bytes()))


def publish_lesson_from_message(message) -> LessonSummary:
    number = lesson_number_from_subject(message.subject or "")
    if number is None:
        raise RuntimeError("Assunto não contém número de lição válido.")
    raw = gemini_json_from_images(message, number)
    lesson = lesson_from_data(raw, number)
    lesson.number = number

    LESSON_DIR.mkdir(parents=True, exist_ok=True)
    page_path = LESSON_DIR / f"{lesson.slug}.html"
    page_path.write_text(render_lesson_page(lesson), encoding="utf-8")
    index_path = update_lesson_index(lesson)
    sitemap_path = update_lesson_sitemap(lesson)
    upload_lesson_files([page_path, index_path, sitemap_path])
    verify_lesson_publication(lesson)
    return lesson


def verify_lesson_publication(lesson: LessonSummary) -> None:
    page_path = f"licoes/{lesson.slug}.html"
    page_url = f"{DOMAIN}/{page_path}"
    page_html = remote_text(page_path)
    index_html = remote_text("licoes-escola-dominical.html")
    sitemap_xml = remote_text("sitemap.xml")
    if (
        f"Lição {lesson.number}" not in page_html
        or page_path not in index_html
        or page_url not in sitemap_xml
    ):
        raise RuntimeError(f"Publicação da Lição {lesson.number} não ficou visível no site.")
