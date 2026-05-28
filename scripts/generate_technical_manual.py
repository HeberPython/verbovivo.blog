from __future__ import annotations

import html
import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_manual_output"
DOMAIN = "https://verbovivo.blog"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def env_values() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in read("automation/.env").splitlines():
        if not line.strip() or line.strip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def git_lines(args: list[str]) -> str:
    try:
        result = subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as exc:
        return f"Nao foi possivel executar git {' '.join(args)}: {exc}"


def file_inventory() -> list[str]:
    ignored = {"_manual_output", ".git", ".vercel", "__pycache__"}
    files: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in ignored for part in path.relative_to(ROOT).parts):
            continue
        files.append(path.relative_to(ROOT).as_posix())
    return sorted(files)


def articles() -> list[dict]:
    draft_dir = ROOT / "_drafts"
    articles_from_drafts: list[dict] = []
    for path in sorted(draft_dir.glob("*.json")):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        slug = item.get("slug")
        if slug and (ROOT / "site" / "artigos" / f"{slug}.html").exists():
            articles_from_drafts.append(
                {
                    "title": item.get("title", ""),
                    "slug": slug,
                    "author": item.get("author", ""),
                    "category": item.get("category", ""),
                    "status": "publicado",
                }
            )
    if articles_from_drafts:
        return articles_from_drafts

    article_dir = ROOT / "site" / "artigos"
    articles_from_html: list[dict] = []
    for path in sorted(article_dir.glob("*.html")):
        text = path.read_text(encoding="utf-8", errors="replace")
        title = re.search(r"<title>(.*?)</title>", text, flags=re.I | re.S)
        author = re.search(r'<p class="author">.*?Por\s+([^<]+)</p>', text, flags=re.I | re.S)
        articles_from_html.append(
            {
                "title": html.unescape(title.group(1).split("|")[0].strip()) if title else path.stem,
                "slug": path.stem,
                "author": html.unescape(author.group(1).strip()) if author else "",
                "category": "",
                "status": "publicado",
            }
        )
    return articles_from_html


def h(text: str) -> str:
    return html.escape(text, quote=True)


def table_html(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{h(item)}</th>" for item in headers)
    body = "\n".join("<tr>" + "".join(f"<td>{h(cell)}</td>" for cell in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def code(text: str) -> str:
    return f"<pre>{h(text)}</pre>"


def build_manual_html(env: dict[str, str]) -> str:
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    inventory = "\n".join(file_inventory())
    article_rows = [
        [
            item.get("title", ""),
            item.get("slug", ""),
            item.get("author", ""),
            item.get("category", ""),
            item.get("status", ""),
        ]
        for item in articles()
    ]
    env_text = "\n".join(f"{key}={value}" for key, value in env.items())
    git_recent = git_lines(["log", "--oneline", "-12"])
    git_remote = git_lines(["remote", "-v"])

    site_map = [
        ["/", "site/index.html", "Pagina inicial, hero, artigo em destaque, grade de reflexoes e linha editorial."],
        ["/sobre.html", "site/sobre.html", "Descricao do projeto e nota sobre autores identificados por artigo."],
        ["/contato.html", "site/contato.html", "Contato publico e formulario mailto para contato@verbovivo.blog."],
        ["/faq.html", "site/faq.html", "Perguntas frequentes e orientacoes editoriais."],
        ["/politica-de-privacidade.html", "site/politica-de-privacidade.html", "Politica em linguagem compatível com LGPD para o estado atual do site."],
        ["/artigos/*.html", "site/artigos/", "Artigos publicados individualmente."],
        ["/revisao.php", "site/revisao.php", "Tela privada por token para aprovar ou corrigir rascunhos."],
        ["/cron-editorial.php", "site/cron-editorial.php", "Script CLI executado pelo Cron Jobs da Hostinger."],
        ["/sitemap.xml", "site/sitemap.xml", "Mapa XML submetido ao Search Console."],
        ["/feed.xml", "site/feed.xml", "Feed RSS dos artigos."],
        ["/robots.txt", "site/robots.txt", "Permissoes de rastreamento e endereco do sitemap."],
        ["/googleb0ae5ae3d773cdee.html", "site/googleb0ae5ae3d773cdee.html", "Arquivo de verificacao do Google Search Console."],
    ]

    tool_rows = [
        ["GitHub", "https://github.com/HeberPython/verbovivo.blog", "Repositorio principal do codigo e historico."],
        ["Hostinger hPanel", "hpanel.hostinger.com", "Dominio, hospedagem, FTP, e-mails e Cron Jobs."],
        ["OpenAI API", "platform.openai.com", "Refino editorial e geracao de imagens."],
        ["Google Search Console", "search.google.com/search-console", "Verificacao, sitemap e acompanhamento de indexacao."],
        ["Codex", "workspace local", "Construcao, manutencao e execucao manual emergencial dos agentes."],
        ["Python", "automation/editorial_agent/", "Agente local, FTP, IMAP, SMTP, OpenAI e scripts de deploy."],
        ["PHP", "public/revisao.php e public/cron-editorial.php", "Aprovacao no site e rotina agendada na Hostinger."],
        ["FTP", env.get("HOSTINGER_FTP_HOST", ""), "Publicacao dos arquivos no public_html da Hostinger."],
        ["IMAP/SMTP Hostinger", "imap.hostinger.com / smtp.hostinger.com", "Leitura e envio de e-mails editoriais."],
    ]

    cron_rows = [
        ["10:00 diariamente", "0 10 * * *", "public_html/cron-editorial.php", "Processa artigo@verbovivo.blog"],
        ["22:00 diariamente", "0 22 * * *", "public_html/cron-editorial.php", "Processa artigo@verbovivo.blog"],
    ]

    email_rows = [
        ["artigo@verbovivo.blog", "Com imagem gerada pelo agente", "Recebe texto bruto, refina, gera imagem e responde com preview e link de aprovacao."],
        ["publicar@verbovivo.blog", "Publicacao direta", "Recebe artigo pronto com imagem anexada. No estado atual, o fluxo direto esta implementado no agente Python e pode ser executado manualmente; o cron PHP prioriza artigo@."],
        ["contato@verbovivo.blog", "Contato publico", "Unico e-mail exibido publicamente na pagina Contato."],
    ]

    paths_rows = [
        ["Workspace Codex", str(ROOT), "Codigo-fonte local e scripts."],
        ["Site estatico gerado", str(ROOT / "site"), "Arquivos finais enviados para a Hostinger."],
        ["Fontes publicas copiadas", str(ROOT / "public"), "Arquivos extras preservados em rebuild."],
        ["Configuracao local secreta", str(ROOT / "automation/.env"), "Credenciais usadas pelo agente Python."],
        ["Configuracao privada no servidor", "/home/u454442761/domains/verbovivo.blog/public_html/_private/editorial-config.php", "Credenciais do cron PHP, bloqueadas por .htaccess."],
        ["Rascunhos no servidor", "/home/u454442761/domains/verbovivo.blog/public_html/_editorial_drafts", "JSONs por token para revisao."],
        ["Artigos publicados", "/home/u454442761/domains/verbovivo.blog/public_html/artigos", "HTML publico dos artigos."],
        ["Imagens dos artigos", "/home/u454442761/domains/verbovivo.blog/public_html/images/articles", "Capas geradas ou anexadas."],
    ]

    author_template = """Autor: Nome do Autor
Instagram: @usuario
Facebook: facebook.com/usuario
YouTube: youtube.com/@canal
X: @usuario
LinkedIn: linkedin.com/in/usuario
Site: meusite.com

Texto do artigo começa aqui..."""

    recipe = """1. Criar/recriar repositorio GitHub verbovivo.blog.
2. Criar estrutura site/, public/, scripts/ e automation/editorial_agent/.
3. Recriar scripts/build_static_site.py com ARTICLES, paginas estaticas, CSS, sitemap, feed e .htaccess.
4. Recriar public/revisao.php para aprovar/corrigir rascunhos por token.
5. Recriar public/cron-editorial.php para rodar em CLI no Cron Jobs da Hostinger.
6. Criar automation/.env local com as credenciais listadas neste manual.
7. Enviar arquivos do site para a Hostinger via FTP ou Git Deploy.
8. Enviar _private/editorial-config.php para o servidor usando automation.editorial_agent.upload_cron_config.
9. Configurar Cron Jobs no hPanel: PHP, public_html/cron-editorial.php, horarios 10:00 e 22:00.
10. Verificar Search Console com googleb0ae5ae3d773cdee.html e enviar sitemap.xml.
11. Enviar artigo teste para artigo@verbovivo.blog, aguardar cron ou rodar manualmente poll-once.
12. Conferir e-mail de resposta, aprovar em /revisao.php e validar se home/feed/sitemap atualizaram."""

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Manual Tecnico Verbo Vivo</title>
  <style>
    :root {{ --ink:#17201b; --muted:#59645c; --sage:#4f7059; --gold:#a9792e; --line:#d8d0bf; --paper:#fbfaf6; --white:#fffdf8; }}
    body {{ margin:0; background:var(--paper); color:var(--ink); font-family:Arial, Helvetica, sans-serif; line-height:1.62; }}
    main {{ max-width:1040px; margin:0 auto; padding:42px 22px 80px; }}
    h1,h2,h3 {{ font-family:Georgia, 'Times New Roman', serif; line-height:1.08; }}
    h1 {{ font-size:42px; margin:0 0 8px; }}
    h2 {{ border-top:2px solid var(--line); margin-top:42px; padding-top:28px; font-size:28px; }}
    h3 {{ color:var(--sage); font-size:20px; margin-top:26px; }}
    .meta {{ color:var(--muted); }}
    .notice {{ border-left:5px solid var(--gold); background:var(--white); padding:14px 18px; }}
    table {{ width:100%; border-collapse:collapse; background:var(--white); margin:14px 0 24px; font-size:14px; }}
    th,td {{ border:1px solid var(--line); padding:10px; text-align:left; vertical-align:top; }}
    th {{ background:#efe6d4; }}
    pre {{ background:#17201b; color:#fffdf8; overflow:auto; padding:16px; white-space:pre-wrap; word-break:break-word; }}
    code {{ background:#efe6d4; padding:2px 4px; }}
    .secret {{ border:2px solid #a9792e; background:#fff8e8; padding:14px 18px; }}
    .small {{ font-size:13px; color:var(--muted); }}
  </style>
</head>
<body>
<main>
  <h1>Manual Tecnico e Operacional do Verbo Vivo</h1>
  <p class="meta">Gerado em {h(now)}. Projeto: <strong>{DOMAIN}</strong>.</p>
  <p class="notice"><strong>Documento reservado.</strong> Este arquivo contem credenciais, enderecos internos, fluxos de automacao e receita de reconstrucao. Manter somente em ambiente local confiavel.</p>

  <h2>1. Visao Geral</h2>
  <p>O Verbo Vivo e um blog cristao estatico com paginas HTML/CSS, hospedado na Hostinger, com automacao editorial por e-mail. O site publica reflexoes, permite revisao por token e atualiza pagina inicial, RSS e sitemap quando um artigo e publicado.</p>

  <h2>2. Ferramentas e Servicos</h2>
  {table_html(["Ferramenta", "Endereco/Local", "Funcao"], tool_rows)}

  <h2>3. Mapa do Site</h2>
  {table_html(["URL", "Arquivo", "Funcao visivel/invisivel"], site_map)}

  <h2>4. Enderecos e Armazenamento</h2>
  {table_html(["Item", "Endereco", "Uso"], paths_rows)}

  <h2>5. E-mails e Fluxos Editoriais</h2>
  {table_html(["Caixa", "Uso", "Comportamento"], email_rows)}
  <h3>Gabarito de envio para autores</h3>
  {code(author_template)}

  <h2>6. Agentes e Automacoes</h2>
  <h3>Agente Python local</h3>
  <p>Implementado em <code>automation/editorial_agent/</code>. Le IMAP, chama OpenAI, gera rascunhos, publica via FTP e pode ser acionado manualmente pelo Codex.</p>
  {code("python -m automation.editorial_agent.worker poll-once\npython -m automation.editorial_agent.worker publish-once\npython -m automation.editorial_agent.deploy_site\npython -m automation.editorial_agent.upload_cron_config")}
  <h3>Agente PHP na Hostinger</h3>
  <p>Implementado em <code>public/cron-editorial.php</code> e publicado como <code>site/cron-editorial.php</code>. Roda via Cron Jobs em modo CLI e nao pode ser acessado pelo navegador.</p>
  {table_html(["Horario", "Cron", "Comando", "Funcao"], cron_rows)}
  <h3>Pagina de revisao</h3>
  <p><code>revisao.php</code> abre rascunhos por token, mostra artigo, imagem e campos para corrigir. Ao aprovar, grava o artigo em <code>/artigos</code>, atualiza a home, <code>feed.xml</code> e <code>sitemap.xml</code>.</p>

  <h2>7. SEO, Google e Descoberta</h2>
  <p>O site possui <code>robots.txt</code>, <code>sitemap.xml</code>, <code>feed.xml</code>, URLs HTML estaveis e arquivo de verificacao do Search Console. O sitemap submetido deve ser <code>{DOMAIN}/sitemap.xml</code>.</p>

  <h2>8. Conteudo Atual</h2>
  {table_html(["Titulo", "Slug", "Autor", "Categoria", "Status"], article_rows)}

  <h2>9. Credenciais e Configuracoes Sensíveis</h2>
  <div class="secret">
    <p><strong>Atencao:</strong> credenciais abaixo foram registradas a pedido do proprietario para recuperacao local. Nao publicar, nao enviar para terceiros e nao versionar no GitHub.</p>
    {code(env_text)}
  </div>

  <h2>10. Receita para Reconstruir do Zero</h2>
  {code(recipe)}

  <h2>11. Estrutura de Arquivos</h2>
  {code(inventory)}

  <h2>12. Historico Git</h2>
  <h3>Remote</h3>
  {code(git_remote)}
  <h3>Ultimos commits</h3>
  {code(git_recent)}

  <h2>13. Observacoes Operacionais</h2>
  <ul>
    <li>O e-mail publico exibido no site e <code>contato@verbovivo.blog</code>.</li>
    <li>A pagina <code>_private</code> deve sempre retornar 403 quando acessada pelo navegador.</li>
    <li>A pagina <code>cron-editorial.php</code> deve retornar 403 no navegador; ela foi feita para CLI/Cron.</li>
    <li>Para autores, o campo <code>Autor:</code> e o principal. Redes sociais sao opcionais e aparecem publicamente se preenchidas.</li>
    <li>Ao trocar senhas de e-mail, FTP ou OpenAI, atualizar <code>automation/.env</code> local e reenviar <code>_private/editorial-config.php</code>.</li>
  </ul>
</main>
</body>
</html>
"""


def plain_from_html(text: str) -> str:
    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = re_sub(r"<(h[1-3]|p|li|tr|table|pre)[^>]*>", "\n", text)
    text = re_sub(r"</(h[1-3]|p|li|tr|table|pre)>", "\n", text)
    text = re_sub(r"<[^>]+>", "", text)
    return html.unescape(text)


def re_sub(pattern: str, repl: str, text: str) -> str:
    import re

    return re.sub(pattern, repl, text, flags=re.IGNORECASE)


def build_pdf(html_text: str, output: Path) -> None:
    styles = getSampleStyleSheet()
    title = ParagraphStyle("VVTitle", parent=styles["Title"], fontName="Times-Bold", fontSize=22, leading=26, spaceAfter=12)
    h2 = ParagraphStyle("VVHeading2", parent=styles["Heading2"], fontName="Times-Bold", fontSize=16, leading=20, spaceBefore=16, spaceAfter=8)
    h3 = ParagraphStyle("VVHeading3", parent=styles["Heading3"], fontName="Times-Bold", fontSize=13, leading=16, spaceBefore=10, spaceAfter=6, textColor=colors.HexColor("#4f7059"))
    normal = ParagraphStyle("VVNormal", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13)
    mono = ParagraphStyle("VVMono", parent=styles["Code"], fontName="Courier", fontSize=7.2, leading=9)
    doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=1.45 * cm, leftMargin=1.45 * cm, topMargin=1.35 * cm, bottomMargin=1.35 * cm)
    story: list = []

    def add_heading(text: str, level: int = 2) -> None:
        story.append(Paragraph(h(text), title if level == 1 else h2 if level == 2 else h3))
        story.append(Spacer(1, 4))

    add_heading("Manual Tecnico e Operacional do Verbo Vivo", 1)
    story.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}. Projeto: {DOMAIN}.", normal))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Documento reservado. Contem credenciais, enderecos internos, fluxos de automacao e receita de reconstrucao.", normal))

    sections = [
        ("Visao Geral", "O Verbo Vivo e um blog cristao estatico com paginas HTML/CSS, hospedado na Hostinger, com automacao editorial por e-mail. O site publica reflexoes, permite revisao por token e atualiza pagina inicial, RSS e sitemap quando um artigo e publicado."),
        ("Ferramentas e Servicos", table_html(["Ferramenta", "Endereco/Local", "Funcao"], tool_rows_for_pdf())),
    ]

    # The PDF is intentionally text-first; tables are flattened for robustness.
    plain = plain_from_html(html_text)
    for chunk in [plain[i : i + 3600] for i in range(0, len(plain), 3600)]:
        story.append(Spacer(1, 8))
        story.append(Preformatted(chunk.strip(), mono))
        if len(chunk) == 3600:
            story.append(PageBreak())

    doc.build(story)


def tool_rows_for_pdf() -> list[list[str]]:
    return []


def build_secret_recipe(env: dict[str, str], output: Path) -> None:
    env_text = "\n".join(f"{key}={value}" for key, value in env.items())
    content = f"""VERBO VIVO - CREDENCIAIS E RECEITA RESERVADA
Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}
Dominio: {DOMAIN}
Repositorio: https://github.com/HeberPython/verbovivo.blog

Credenciais atuais:
{env_text}

Comandos essenciais:
python -m automation.editorial_agent.worker poll-once
python -m automation.editorial_agent.worker publish-once
python -m automation.editorial_agent.deploy_site
python -m automation.editorial_agent.upload_cron_config

Cron Jobs na Hostinger:
0 10 * * * public_html/cron-editorial.php
0 22 * * * public_html/cron-editorial.php

Receita curta de reconstrucao:
1. Clonar ou recriar o repositorio.
2. Recriar automation/.env com as credenciais acima.
3. Instalar dependencias de automation/requirements.txt.
4. Rodar scripts/build_static_site.py.
5. Enviar site/ para public_html via FTP.
6. Rodar upload_cron_config.py para recriar _private/editorial-config.php.
7. Conferir _private e cron-editorial.php retornando 403 pelo navegador.
8. Configurar cron no hPanel nos horarios 10h e 22h.
9. Enviar artigo teste para artigo@verbovivo.blog.
"""
    output.write_text(content, encoding="utf-8")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    env = env_values()
    html_text = build_manual_html(env)
    html_path = OUT / "Manual_Tecnico_Verbo_Vivo.html"
    pdf_path = OUT / "Manual_Tecnico_Verbo_Vivo.pdf"
    secret_path = OUT / "VERBO_VIVO_CREDENCIAIS_E_RECEITA.txt"
    html_path.write_text(html_text, encoding="utf-8")
    build_pdf(html_text, pdf_path)
    build_secret_recipe(env, secret_path)
    print(html_path)
    print(pdf_path)
    print(secret_path)


if __name__ == "__main__":
    main()
