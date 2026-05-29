from __future__ import annotations

import base64
import json
import secrets
from html import escape
from io import BytesIO
from pathlib import Path

from openai import OpenAI
from openai import OpenAIError
from PIL import Image

from .config import settings
from .content import extract_submission_metadata, fallback_refine, slugify, webp_name
from .models import ArticleDraft


SYSTEM_PROMPT = """
Você é o editor cristão do blog Verbo Vivo.
Recebe textos brutos escritos por humanos e transforma em uma reflexão curta,
acolhedora, inteligível e biblicamente coerente.

Regras:
- Preserve a intenção espiritual do autor.
- Não invente fatos biográficos, citações ou referências bíblicas.
- Não faça sensacionalismo bíblico.
- Não mencione IA, automação ou agente.
- Escreva em português do Brasil.
- O tom deve ser pastoral, claro, reverente e acessível.
- Compacte o texto bruto em uma reflexão publicável, sem perder o contexto bíblico central.
- Escreva referências bíblicas por extenso: "Mateus, capítulo 21, versículo 17" ou "Filipenses, capítulo 2, versículos 14 a 16", nunca no formato "21:17".
"""


def refine_with_openai(source_text: str, subject: str, sender: str) -> ArticleDraft:
    metadata, article_text = extract_submission_metadata(source_text)
    if not settings.openai_api_key:
        return fallback_refine(source_text, subject, sender)

    client = OpenAI(api_key=settings.openai_api_key)
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Transforme o texto abaixo em artigo reflexivo para o Verbo Vivo. "
                        "Responda somente JSON válido com as chaves: title, category, excerpt, quote, "
                        "sections, image_prompt. sections deve ser uma lista de objetos com heading e paragraphs.\n\n"
                        f"Assunto do e-mail: {subject}\n\nTexto bruto:\n{article_text}"
                    ),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
    except OpenAIError as exc:
        print(f"OpenAI unavailable, using fallback draft: {exc.__class__.__name__}")
        return fallback_refine(source_text, subject, sender)
    raw = response.choices[0].message.content or "{}"
    data = json.loads(raw)
    title = data.get("title") or subject or "Nova reflexão"
    sections = data.get("sections") or []
    body_parts = []
    if data.get("quote"):
        body_parts.append(f"<blockquote>{escape(str(data['quote']))}</blockquote>")
    for section in sections:
        heading = str(section.get("heading", "")).strip()
        if heading:
            body_parts.append(f"<h2>{escape(heading)}</h2>")
        for paragraph in section.get("paragraphs", []):
            body_parts.append(f"<p>{escape(str(paragraph))}</p>")

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
        excerpt=data.get("excerpt") or "Uma reflexão cristã para fortalecer a fé na vida cotidiana.",
        category=data.get("category") or "Reflexão",
        author=metadata["author"] or "Autor informado na publicação",
        body_html="\n".join(body_parts),
        image_prompt=data.get("image_prompt") or f"Imagem cristã reverente para o tema: {title}",
        image_filename=f"{slug}-{draft_id}.png",
        author_socials=metadata["socials"],
    )


def generate_cover_image(draft: ArticleDraft, output_dir: Path) -> Path | None:
    if not settings.openai_api_key:
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / draft.image_filename
    client = OpenAI(api_key=settings.openai_api_key)
    try:
        result = client.images.generate(
            model="gpt-image-1",
            prompt=(
                "Crie uma imagem editorial cristã de alta qualidade, realista e nítida, "
                "com vida visual, contraste natural, cores profundas e luz cinematográfica suave. "
                "A imagem deve parecer fotografia/editorial premium, sem aspecto leitoso, sem neblina artificial, "
                "sem desfoque, sem baixa resolução, sem pintura borrada e sem texto escrito na imagem. "
                "Evite rostos em close, evite retratar Jesus de forma literal e evite elementos clichês excessivos. "
                "Use composição clara, profundidade realista, detalhes definidos, atmosfera reverente e esperançosa. "
                f"Contexto bíblico/reflexivo para orientar a cena: {draft.image_prompt}"
            ),
            size="1536x1024",
        )
    except OpenAIError as exc:
        print(f"Image generation unavailable: {exc.__class__.__name__}")
        return None
    image_base64 = result.data[0].b64_json
    if not image_base64:
        return None
    image_bytes = base64.b64decode(image_base64)
    path.write_bytes(image_bytes)
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image.convert("RGB").save(path.with_name(webp_name(path.name)), "WEBP", quality=78, method=6)
    except OSError:
        pass
    draft.local_image_path = str(path)
    return path
