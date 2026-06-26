from __future__ import annotations

import base64
import json
import secrets
import urllib.error
import urllib.request
from html import escape
from pathlib import Path

from openai import OpenAI
from openai import OpenAIError

from .config import settings
from .content import extract_submission_metadata, fallback_refine, slugify, submission_author, submission_socials
from .models import ArticleDraft


SYSTEM_PROMPT = """
VocÃª Ã© o editor cristÃ£o do blog Verbo Vivo.
Recebe textos brutos escritos por humanos e transforma em uma reflexÃ£o curta,
acolhedora, inteligÃ­vel e biblicamente coerente.

Regras:
- Preserve a intenÃ§Ã£o espiritual do autor.
- NÃ£o invente fatos biogrÃ¡ficos, citaÃ§Ãµes ou referÃªncias bÃ­blicas.
- NÃ£o faÃ§a sensacionalismo bÃ­blico.
- NÃ£o mencione IA, automaÃ§Ã£o ou agente.
- Escreva em portuguÃªs do Brasil.
- O tom deve ser pastoral, claro, reverente e acessÃ­vel.
- Compacte o texto bruto em uma reflexÃ£o publicÃ¡vel, sem perder o contexto bÃ­blico central.
- Escreva referÃªncias bÃ­blicas por extenso: "Mateus, capÃ­tulo 21, versÃ­culo 17" ou "Filipenses, capÃ­tulo 2, versÃ­culos 14 a 16", nunca no formato "21:17".
- Mantenha title como tÃ­tulo editorial bonito para aparecer no artigo.
- Crie seo_title com atÃ© 60 caracteres, mais pesquisÃ¡vel no Google, sem sensacionalismo.
- Crie excerpt/seo_description com atÃ© 155 caracteres, claro, fiel ao texto e com termos que pessoas buscariam.
- Crie seo_keywords com uma expressÃ£o principal de busca, curta e natural.
"""


IMAGE_STYLE_PROMPT = (
    "Crie uma imagem editorial cristã premium para o blog Verbo Vivo, com aparência viva, nítida e realista, "
    "semelhante às melhores imagens enviadas prontas para publicação: cores ricas e naturais, contraste bem definido, "
    "luz cinematográfica quente, textura visível, profundidade de campo controlada e composição limpa. "
    "Priorize cenas simbólicas cristãs com paisagens reais, caminhos, luz natural, céu dramático, pedras, oliveiras, "
    "madeira, pergaminho, arquitetura antiga e mãos em oração quando fizer sentido, sempre com atmosfera reverente e esperançosa. "
    "A imagem não pode parecer leitosa, embaçada, lavada, genérica, infantil, caricata, aquarela, pintura borrada, "
    "baixa resolução, stock artificial ou ilustração sem vida. Não inclua texto escrito, letras, marcas, logotipos, "
    "versículos na imagem, rostos em close, representação literal de Jesus, mãos deformadas ou elementos exageradamente clichês. "
    "Use enquadramento horizontal editorial 3:2, sujeito claro, fundo harmonioso e qualidade visual pronta para capa de artigo. "
)


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
                        "Responda somente JSON vÃ¡lido com as chaves: title, seo_title, category, excerpt, "
                        "seo_description, seo_keywords, quote, sections, image_prompt. "
                        "sections deve ser uma lista de objetos com heading e paragraphs.\n\n"
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
    title = data.get("title") or subject or "Nova reflexÃ£o"
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
        excerpt=data.get("excerpt") or "Uma reflexÃ£o cristÃ£ para fortalecer a fÃ© na vida cotidiana.",
        category=data.get("category") or "ReflexÃ£o",
        author=submission_author(metadata),
        body_html="\n".join(body_parts),
        image_prompt=data.get("image_prompt") or f"Imagem cristÃ£ reverente para o tema: {title}",
        image_filename=f"{slug}-{draft_id}.png",
        author_socials=submission_socials(metadata),
        seo_title=data.get("seo_title") or "",
        seo_description=data.get("seo_description") or data.get("excerpt") or "",
        seo_keywords=data.get("seo_keywords") or "",
    )


def generate_cover_image(draft: ArticleDraft, output_dir: Path) -> Path | None:
    if settings.image_provider == "gemini":
        gemini_path = generate_cover_image_with_gemini(draft, output_dir)
        if gemini_path:
            return gemini_path
    return generate_cover_image_with_openai(draft, output_dir)


def generate_cover_image_with_gemini(draft: ArticleDraft, output_dir: Path) -> Path | None:
    if not settings.gemini_api_key:
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / draft.image_filename
    prompt = IMAGE_STYLE_PROMPT + f"Contexto bíblico/reflexivo para orientar a cena: {draft.image_prompt}"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_image_model}:generateContent"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
        },
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": settings.gemini_api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        message = gemini_http_error_message(exc)
        print(f"Gemini image generation unavailable ({exc.code}): {message}")
        return None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"Gemini image generation unavailable, falling back to OpenAI: {exc.__class__.__name__}")
        return None

    image_base64 = first_gemini_image_base64(data)
    if not image_base64:
        print("Gemini image generation returned no image, falling back to OpenAI.")
        return None
    path.write_bytes(base64.b64decode(image_base64))
    draft.local_image_path = str(path)
    return path


def first_gemini_image_base64(data: dict) -> str:
    for candidate in data.get("candidates", []):
        content = candidate.get("content") or {}
        for part in content.get("parts", []):
            inline_data = part.get("inlineData") or part.get("inline_data") or {}
            mime_type = inline_data.get("mimeType") or inline_data.get("mime_type") or ""
            image_data = inline_data.get("data") or ""
            if image_data and mime_type.startswith("image/"):
                return image_data
    return ""


def gemini_http_error_message(exc: urllib.error.HTTPError) -> str:
    try:
        payload = json.loads(exc.read().decode("utf-8"))
        message = str((payload.get("error") or {}).get("message") or "erro sem mensagem")
    except (json.JSONDecodeError, UnicodeDecodeError):
        message = "resposta de erro nao reconhecida"
    return " ".join(message.split())[:500]


def generate_cover_image_with_openai(draft: ArticleDraft, output_dir: Path) -> Path | None:
    if not settings.openai_api_key:
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / draft.image_filename
    client = OpenAI(api_key=settings.openai_api_key)
    try:
        result = client.images.generate(
            model="gpt-image-1",
            prompt=IMAGE_STYLE_PROMPT + f"Contexto bíblico/reflexivo para orientar a cena: {draft.image_prompt}",
            size="1536x1024",
        )
    except OpenAIError as exc:
        print(f"Image generation unavailable: {exc.__class__.__name__}")
        return None
    image_base64 = result.data[0].b64_json
    if not image_base64:
        return None
    path.write_bytes(base64.b64decode(image_base64))
    draft.local_image_path = str(path)
    return path
