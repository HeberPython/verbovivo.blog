# Mural de regras para manutencao

O arquivo `AGENTS.md` na raiz do projeto e a fonte ativa destas regras. Ele deve ser lido antes de qualquer intervencao.

## Principio central

Nenhuma correcao pontual pode fazer um artigo aprovado desaparecer. O catalogo real da Hostinger deve ser sincronizado antes de reconstruir a home, o acervo de artigos, o RSS ou o sitemap.

Desde 01/09/2026, a home deve ser enxuta: somente os 4 artigos mais recentes ficam na pagina inicial. Todos os artigos publicados precisam continuar protegidos e acessiveis em `artigos.html`, no feed e no sitemap.

## Checklist obrigatorio

- Criar backup remoto antes de qualquer deploy ou intervencao que possa alterar o site publicado.
- Auditar antes.
- Preservar paginas e imagens existentes.
- Reconstruir indices a partir do catalogo remoto completo.
- Confirmar que a home tem no maximo 4 artigos e que `artigos.html` contem o acervo completo.
- Bloquear reducao ou divergencia.
- Implantar.
- Auditar novamente no servidor.
