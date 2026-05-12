# Verbo Vivo

Primeira versão publicável do `verbovivo.blog`.

## Site pronto

Abra no navegador:

`site/index.html`

A pasta `site/` contém a home, as páginas dos artigos, imagens, RSS, sitemap, robots.txt e páginas institucionais.

## Reconstruir o site

Use o script:

```powershell
C:\Users\Heber\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\build_static_site.py
```

O script lê os PDFs humanos em `C:\Users\Heber\Documents\verbovivo.blog`, copia as imagens e recria a pasta `site/`.

## Conteúdo inicial

- Depois da Festa: onde ficou Jesus?
- Feitos para brilhar pela Palavra da Vida
- O coração desordenado

Os artigos publicados no site são versões reflexivas e compactadas, preparadas a partir dos textos brutos originais.

## Páginas institucionais

- `site/sobre.html`
- `site/faq.html`
- `site/politica-de-privacidade.html`

## Capas geradas

- `public/images/articles/depois-da-festa.png`
- `public/images/articles/feitos-para-brilhar.png`
- `public/images/articles/coracao-desordenado.png`

## Fluxo editorial proposto

1. O autor adiciona o artigo humano em PDF, DOCX ou Markdown.
2. Um agente extrai o texto e preserva a voz do autor.
3. O agente gera resumo, categoria, tags, imagem contextual, alt text e metadados SEO.
4. O artigo entra como rascunho para aprovação.
5. O site publica somente conteúdo aprovado.
