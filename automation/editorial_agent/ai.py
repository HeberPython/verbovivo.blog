from __future__ import annotations

import base64
import json
import secrets
from pathlib import Path

from openai import OpenAI
from openai import OpenAIError

from .config import settings
from .content import fallback_refine, slugify
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
"""


def refine_with_openai(source_text: str, subject: str, sender: str) -> ArticleDraft:
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
                        f"Assunto do e-mail: {subject}\n\nTexto bruto:\n{source_text}"
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
        body_parts.append(f"<blockquote>{data['quote']}</blockquote>")
    for section in sections:
        heading = section.get("heading", "").strip()
        if heading:
            body_parts.append(f"<h2>{heading}</h2>")
        for paragraph in section.get("paragraphs", []):
            body_parts.append(f"<p>{paragraph}</p>")

    slug = slugify(title)
    return ArticleDraft(
        id=secrets.token_hex(8),
        token=secrets.token_urlsafe(24),
        sender=sender,
        source_subject=subject,
        source_text=source_text,
        title=title,
        slug=slug,
        excerpt=data.get("excerpt") or "Uma reflexão cristã para fortalecer a fé na vida cotidiana.",
        category=data.get("category") or "Reflexão",
        author="Pastor Antonio Lemos Filho",
        body_html="\n".join(body_parts),
        image_prompt=data.get("image_prompt") or f"Imagem cristã reverente para o tema: {title}",
        image_filename=f"{slug}.png",
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
                "Crie uma imagem editorial cristã, reverente, sem texto escrito na imagem, "
                "sem retratar Jesus de forma literal, com atmosfera contemplativa e adequada "
                f"ao contexto bíblico/reflexivo: {draft.image_prompt}"
            ),
            size="1536x1024",
        )
    except OpenAIError as exc:
        print(f"Image generation unavailable: {exc.__class__.__name__}")
        return None
    image_base64 = result.data[0].b64_json
    if not image_base64:
        return None
    path.write_bytes(base64.b64decode(image_base64))
    return path
