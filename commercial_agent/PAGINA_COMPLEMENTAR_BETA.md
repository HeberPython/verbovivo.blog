# Pagina Complementar Beta - Central do Comprador

Nome:

**Central do Comprador - Verbo Vivo Lab**

Objetivo:

Entregar links, atualizacoes e materiais de apoio sem transformar o produto beta em curso grande.

## Estrutura da pagina

### 1. Boas-vindas

Voce entrou no beta do Verbo Vivo Lab. Comece pelo PDF principal e use os checklists como apoio pratico. Esta pagina sera atualizada com erratas, respostas e materiais complementares do beta.

### 2. Downloads

- Ebook PDF.
- Checklist dominio e hospedagem.
- Checklist GitHub e arquivos.
- Checklist e-mails editoriais.
- Checklist SEO.
- Checklist seguranca.
- Checklist paginas ocultas e manutencao.
- Templates de e-mail.
- Planilha de metricas.

### 3. Ordem recomendada

1. Leia a introducao e o mapa do sistema.
2. Defina a funcao do seu blog.
3. Escolha dominio e hospedagem.
4. Modele seus e-mails editoriais.
5. Desenhe aprovacao humana.
6. Publique um artigo simples.
7. Revise SEO e seguranca.
8. Teste as paginas ocultas e o fluxo de autorizacao de remetentes.

### 4. Links uteis

- Blog real: `https://verbovivo.blog`
- Hotmart: `https://app.hotmart.com`
- GitHub: `https://github.com`
- Hostinger hPanel: `https://hpanel.hostinger.com`
- Google Search Console: `https://search.google.com/search-console`
- OpenAI Platform: `https://platform.openai.com`

### 5. FAQ vivo do beta

Adicionar aqui perguntas reais dos compradores.

Perguntas iniciais:

- Preciso saber programar?
- Posso usar WordPress?
- Posso usar outro provedor alem da Hostinger?
- Quanto custa manter algo parecido?
- Posso adaptar para outro nicho?
- Como evito que qualquer pessoa publique no meu blog?
- O que e uma pagina oculta por token?
- Por que preciso testar o gestor, a revisao e o cron mesmo quando a home esta funcionando?
- O que fazer se a hospedagem retornar erro 500 em uma pagina PHP?

### 6. Aviso de seguranca

Nao publique senhas, tokens, chaves de API, arquivos `.env`, configuracoes privadas, prints com credenciais ou dados de acesso. O produto ensina a arquitetura e o processo; nao compartilhe credenciais do seu projeto.

### 7. Feedback

Perguntas para compradores:

1. O que ficou mais claro para voce?
2. O que ainda parece dificil?
3. Qual capitulo deveria virar video?
4. Voce pretende implementar sozinho ou com ajuda tecnica?
5. O preco beta fez sentido para a entrega?

### 8. Atualizacoes do caso real

Registrar nesta area as mudancas reais do `verbovivo.blog` que acontecerem depois da publicacao do PDF.

Atualizacao inicial recomendada:

- O blog passou a usar lista de remetentes autorizados para os e-mails editoriais.
- Remetentes novos precisam ser autorizados manualmente, de forma temporaria ou permanente.
- O gestor oculto de artigos existe, mas permanece simples e protegido por token.
- A manutencao do projeto agora inclui teste obrigatorio das paginas ocultas.
- Foi adicionada medicao propria anonima em `analytics.php`.
- Foi documentado um erro real de producao: arquivo PHP com BOM invisivel antes de `<?php`, causando erro 500. A correcao foi regravar os PHPs sem BOM e validar online.
