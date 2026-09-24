from __future__ import annotations

import base64
import json
import re
import secrets
import time
import urllib.error
import urllib.request
from html import escape
from pathlib import Path

from openai import OpenAI
from openai import OpenAIError

from .config import settings
from .content import extract_submission_metadata, slugify, submission_author, submission_socials
from .models import ArticleDraft
from .text_quality import EditorialTextError, validate_reflection


IMAGE_ERA_GUARDRAILS = """

COERENCIA DE EPOCA DA CENA (apenas direcao de imagem, sem alterar o artigo):
- Defina a epoca pela cena e pelo contexto do artigo, nao apenas por haver uma citacao biblica ou um simbolo cristao.
- Quando a cena representar os dias atuais, uma aplicacao contemporanea ou pessoas com roupas atuais, use ambientes modernos coerentes: arquitetura, mobiliario, objetos, ruas e casas da mesma epoca das roupas.
- Se uma cena atual ocorrer em um templo, represente uma igreja contemporanea semelhante as de hoje, com arquitetura e mobiliario atuais; nao use igrejas antigas de pedra, ruinas, mosteiros ou cenarios dos primeiros seculos como fundo padrao para personagens modernos.
- Quando o contexto da cena for historico, biblico ou dos primeiros seculos da igreja, mantenha a ambientacao historica: roupas, construcoes, templos e objetos coerentes com aquela epoca. Nao modernize essas cenas.
- Nao misture roupas atuais com ambientacao antiga sem uma justificativa historica explicita no artigo. Uma simples referencia biblica nao obriga a ambientar a aplicacao atual na Antiguidade.
- Preserve os simbolos centrais e a identidade visual especifica do artigo dentro da epoca escolhida. Exemplos anteriores de arquitetura antiga ou biblica so se aplicam quando a cena for historica.
"""


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
- Produza uma reflexÃ£o substancial e autossuficiente, normalmente entre 550 e 900 palavras, desde que o texto-fonte ofereÃ§a conteÃºdo para isso. NÃ£o alongue com repetiÃ§Ãµes ou frases vazias.
- DÃª a cada artigo uma contribuiÃ§Ã£o prÃ³pria: evite introduÃ§Ãµes, subtÃ­tulos, conclusÃµes e aplicaÃ§Ãµes genÃ©ricas ou reaproveitadas de outros textos.
- Organize a leitura com uma abertura que apresente a pergunta central, desenvolvimento bÃ­blico claro, aplicaÃ§Ã£o concreta e conclusÃ£o coerente.
- Quando o texto-fonte trouxer livros, autores, dicionÃ¡rios ou outras fontes, preserve essas referÃªncias para aprofundamento. Nunca invente fontes para completar o artigo.
- Diferencie com clareza a explicaÃ§Ã£o do texto bÃ­blico, a reflexÃ£o pastoral e a aplicaÃ§Ã£o prÃ¡tica.
- Escreva referÃªncias bÃ­blicas por extenso: "Mateus, capÃ­tulo 21, versÃ­culo 17" ou "Filipenses, capÃ­tulo 2, versÃ­culos 14 a 16", nunca no formato "21:17".
- Mantenha title como tÃ­tulo editorial bonito para aparecer no artigo.
- Crie seo_title com atÃ© 60 caracteres, mais pesquisÃ¡vel no Google, sem sensacionalismo.
- Crie excerpt/seo_description com atÃ© 155 caracteres, claro, fiel ao texto e com termos que pessoas buscariam.
- Crie seo_keywords com uma expressÃ£o principal de busca, curta e natural.
- Crie image_prompt como uma cena concreta, humana e cinematogrÃ¡fica, nÃ£o como uma lista de sÃ­mbolos.
- O image_prompt deve ter assinatura visual prÃ³pria: lugar especÃ­fico, hora do dia, personagem ou grupo, aÃ§Ã£o observÃ¡vel, objeto integrado Ã cena e emoÃ§Ã£o pastoral do artigo.
- NÃ£o use image_prompt genÃ©rico como "pessoas caminhando", "homem orando", "paisagem bÃ­blica", "luz dourada", "estrada ao pÃ´r do sol", "cruz no horizonte", "mesa com BÃ­blia" sem uma razÃ£o direta no texto.
- Evite image_prompt com objetos isolados como coroa, pedra, pergaminho, coraÃ§Ã£o, espada, chave, raio de luz ou cruz como protagonista literal. Esses elementos sÃ³ podem aparecer discretamente como apoio da cena, se forem necessÃ¡rios.
- Quando o titulo ou o texto tiver um simbolo teologico central, como pedra angular, fundamento, videira, pao da vida, caminho, luz, coroa, armadura ou cruz, preserve esse simbolo como parte organica da cena. Nao substitua o simbolo central por uma cena generica de caminhada, grupo ou comunidade.
- Para temas sobre pedra angular, fundamento ou ressurreicao, quando a cena for historica, use arquitetura antiga, base de pedra, tumulo vazio, amanhecer, caminho e pessoas em contemplacao como cena integrada, sem teatralidade, brilho magico ou literalidade cafona. Se a cena for uma aplicacao atual, integre o simbolo a um ambiente contemporaneo coerente.
""" + IMAGE_ERA_GUARDRAILS


IMAGE_STYLE_PROMPT = (
    "Crie uma imagem editorial cristã premium para o blog Verbo Vivo, com aparência viva, nítida, realista e cinematográfica. "
    "A imagem deve parecer uma cena fotografada ou filmada com direção de arte refinada, não uma ilustração religiosa genérica. "
    "Priorize uma cena concreta com narrativa visual: pessoas em oração, serviço, caminhada, espera, consolo, discipulado, leitura bíblica, "
    "família, trabalho humilde, comunidade, paisagens bíblicas realistas ou ambientes pastorais iluminados por luz natural. "
    "Use cores ricas e naturais, contraste bem definido, textura visível, pele e tecidos realistas, profundidade de campo controlada, "
    "composição limpa e luz cinematográfica quente, como fim de tarde ou amanhecer. "
    "Quando o artigo tiver um símbolo teológico central, represente-o como elemento visual integrado e necessário à cena, "
    "como fundamento de pedra, videira, caminho, luz natural, mesa, pão, água, campo, casa ou arquitetura bíblica realista. "
    "Não substitua o símbolo central por uma cena genérica de caminhada, grupo ou comunidade. "
    "Símbolos cristãos secundários podem existir apenas como detalhes discretos e integrados à cena. Não transforme conceitos abstratos do título em objetos literais. "
    "Evite objetos isolados como coroa, pedra, pergaminho, coração, chave, espada, raio de luz, cruz gigante ou brilho saindo de objetos. "
    "A imagem não pode parecer leitosa, embaçada, lavada, plástica, artificial, teatral, infantil, caricata, aquarela, pintura borrada, "
    "baixa resolução, stock genérico, capa religiosa clichê ou ilustração sem vida. Não inclua texto escrito, letras, marcas, logotipos, "
    "versículos na imagem, rostos em close, representação literal de Jesus, mãos deformadas ou efeitos sobrenaturais exagerados. "
    "Use enquadramento horizontal editorial 3:2, sujeito claro, fundo harmonioso e qualidade visual pronta para capa de artigo. "
)


GENERIC_IMAGE_GUARDRAILS = """

DIRECAO VISUAL OBRIGATORIA PARA NAO GERAR CAPA GENERICA:
- A imagem precisa ser imediatamente distinguivel das outras capas do blog quando vista em uma grade.
- Crie uma cena unica baseada no titulo, no resumo e no corpo do artigo, nao uma imagem devocional padrao.
- Use pelo menos quatro detalhes concretos do artigo para decidir ambiente, personagem, acao, objeto e clima.
- Escolha uma composicao especifica: interior, exterior, mesa, rua, casa, oficina, deserto, cidade antiga, campo, beira-mar, templo ou comunidade somente se isso nascer do texto.
- Varie camera, distancia, luz, quantidade de pessoas, arquitetura, cor dominante e gesto humano.
- Proibido usar por padrao: pessoa isolada orando em paisagem bonita, estrada de terra ao por do sol, cruz no horizonte, pedra iluminada, oliveiras genericas, pergaminho, Biblia aberta decorativa, feixes magicos de luz, silhuetas sem identidade visual, grupo sentado conversando sem relacao direta com o tema.
- Se o artigo realmente exigir pedra, caminho, luz, cruz, mesa ou Biblia, use esse elemento como parte organica de uma cena especifica, nunca como objeto decorativo isolado.
- A imagem deve ter nitidez alta, contraste vivo, cor natural rica, textura realista e atmosfera contemporanea/editorial, sem aparencia leitosa, lavada, embaçada ou envelhecida.
"""


def plain_text_from_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    return " ".join(text.split())


def build_image_generation_prompt(draft: ArticleDraft) -> str:
    article_context = "\n".join(
        part.strip()
        for part in [
            f"Titulo: {draft.title}",
            f"Resumo: {draft.excerpt}",
            f"Direcao visual proposta pelo editor: {draft.image_prompt}",
            f"Trecho do artigo: {plain_text_from_html(draft.body_html)[:1200]}",
        ]
        if part.strip()
    )
    return (
        IMAGE_STYLE_PROMPT
        + GENERIC_IMAGE_GUARDRAILS
        + IMAGE_ERA_GUARDRAILS
        + "\nCONTEXTO ESPECIFICO DO ARTIGO:\n"
        + article_context
        + "\n\nAntes de imaginar a imagem, escolha mentalmente qual detalhe torna este artigo diferente dos demais e faça esse detalhe aparecer na cena."
    )


def refine_with_openai(source_text: str, subject: str, sender: str) -> ArticleDraft:
    metadata, article_text = extract_submission_metadata(source_text)
    if not settings.openai_api_key:
        raise EditorialTextError('Text service key missing; original remains pending.')

    client = OpenAI(api_key=settings.openai_api_key, max_retries=0, timeout=90)
    response = request_editorial_completion(client,
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
    if response.choices[0].finish_reason != 'stop':
        raise EditorialTextError('Text response did not finish normally; draft blocked.')
    raw = response.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise EditorialTextError('Invalid structured text response; draft blocked.') from None
    if not isinstance(data, dict) or not isinstance(data.get('sections'), list):
        raise EditorialTextError('Missing editorial sections; draft blocked.')
    title = data.get("title") or subject or "Nova reflexÃ£o"
    sections = data.get("sections") or []
    body_parts = []
    if data.get("quote"):
        body_parts.append(f"<blockquote>{escape(str(data['quote']))}</blockquote>")
    for section in sections:
        if not isinstance(section, dict) or not isinstance(section.get('paragraphs'), list):
            raise EditorialTextError('Invalid editorial section; draft blocked.')
        heading = str(section.get("heading", "")).strip()
        if heading:
            body_parts.append(f"<h2>{escape(heading)}</h2>")
        for paragraph in section.get("paragraphs", []):
            body_parts.append(f"<p>{escape(str(paragraph))}</p>")

    validate_reflection(article_text, "\n".join(body_parts))
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


def request_editorial_completion(client, **kwargs):
    for attempt in range(3):
        try:
            return client.chat.completions.create(**kwargs)
        except OpenAIError as exc:
            details = getattr(exc, 'body', None)
            details = details if isinstance(details, dict) else {}
            details = details.get('error', details)
            details = details if isinstance(details, dict) else {}
            code = getattr(exc, 'code', None) or details.get('code')
            status = getattr(exc, 'status_code', None)
            message = str(details.get('message', '')).lower()
            quota = code in {'insufficient_quota', 'billing_hard_limit_reached', 'credit_balance_exhausted'} or 'exceeded your current quota' in message
            transient = status == 429 or (isinstance(status, int) and status >= 500)
            transient = transient or exc.__class__.__name__ in {'APIConnectionError', 'APITimeoutError'}
            # Log classification only, never request bodies, credentials or full provider errors.
            reason = 'quota_or_billing' if quota else ('temporary_limit_or_connection' if transient else 'provider_error')
            safe_code = str(code) if re.fullmatch('[a-z_]{1,80}', str(code)) else 'unknown'
            limits = re.findall(r'\b(limit|used|requested)\s*:?\s*([0-9.,]+)', message)
            units = [unit for unit in ['tokens per min', 'requests per min', 'tokens per day', 'requests per day'] if unit in message]
            print(f'Text generation blocked: {exc.__class__.__name__}; reason={reason}; code={safe_code}; limits={limits}; units={units}; attempt={attempt + 1}', flush=True)
            if quota or not transient or attempt == 2:
                raise EditorialTextError(f'Text generation failed ({reason}); no approval draft created.') from None
            headers = getattr(getattr(exc, 'response', None), 'headers', {})
            retry_after = headers.get('retry-after', '')
            delay = min(60, max(5, float(retry_after))) if re.fullmatch(r'\d+(?:\.\d+)?', retry_after) else 5 * (attempt + 1)
            time.sleep(delay)


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
    prompt = build_image_generation_prompt(draft)
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
            prompt=build_image_generation_prompt(draft),
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
