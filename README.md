# Verbo Vivo

Código-fonte do blog cristão `verbovivo.blog`.

## Estrutura principal

- `site/`: versão final publicada na Hostinger.
- `public/`: arquivos PHP e assets preservados para publicação.
- `automation/editorial_agent/`: agente editorial por e-mail, revisão, geração de imagem e publicação.
- `scripts/build_static_site.py`: recompõe a home, os três artigos atuais, `feed.xml` e `sitemap.xml`.
- `_drafts/`: rascunhos JSON usados pelo fluxo editorial.

## Recriar a versão estática atual

```powershell
python scripts\build_static_site.py
```

O script usa os rascunhos atuais em `_drafts/`, recompõe `site/index.html`, gera as páginas em `site/artigos/`, copia imagens e atualiza RSS/sitemap.

## Artigos atuais da home

- O Coração Desordenado: Guardando a Fonte da Vida
- Feitos para Brilhar: Vivendo a Palavra da Vida em Meio à Geração
- Depois da festa: onde ficou Jesus?

## Fluxo editorial

1. `artigo@verbovivo.blog`: recebe texto, refina, gera imagem e devolve preview para aprovação.
2. `publicar@verbovivo.blog`: recebe artigo pronto com imagem e adapta ao layout do site.
3. `revisao.php`: permite aprovar ou corrigir um rascunho por token.
4. `cron-editorial.php`: executa a leitura editorial na Hostinger via Cron Jobs.

Credenciais ficam fora do Git em `automation/.env` e no arquivo privado do servidor.
