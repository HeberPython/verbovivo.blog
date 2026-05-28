# Memorial compacto do projeto Verbo Vivo

Atualizado em: 2026-05-28

Este arquivo resume o que é imprescindível para retomar o projeto em uma conversa nova, sem depender do histórico longo do Codex.

## Projeto

- Site: `https://verbovivo.blog`
- Repositório GitHub: `https://github.com/HeberPython/verbovivo.blog`
- Workspace local: `C:\Users\Heber\Documents\Codex\2026-05-10\com-o-claude-code-eu-fiz\verbovivo-blog`
- Hospedagem final: Hostinger, pasta `public_html`
- Domínio: `verbovivo.blog`
- Linha editorial: reflexões cristãs, textos bíblicos, fé, consolo, formação espiritual e vida cristã.
- Crédito no rodapé: `By @tec.agora`

## Estrutura ativa do repositório

- `site/`: versão publicada no servidor.
- `public/`: arquivos PHP e assets espelhados usados para publicação.
- `automation/editorial_agent/`: agente editorial, leitura de e-mails, geração/refino, publicação e relatórios.
- `scripts/build_static_site.py`: recompõe a home atual, artigos atuais, RSS e sitemap.
- `commercial_agent/`: materiais comerciais, roteiro do ebook, Hotmart, copy e validação.
- `docs/`: memoriais, decisões e notas de continuidade.

## Artigos atuais da home

1. `O Coração Desordenado: Guardando a Fonte da Vida`
   - Slug: `o-coracao-desordenado-guardando-a-fonte-da-vida`
   - Imagem: `o-coracao-desordenado-guardando-a-fonte-da-vida-dcf1e0e616343e53.png`
2. `Feitos para Brilhar: Vivendo a Palavra da Vida em Meio à Geração`
   - Slug: `feitos-para-brilhar-vivendo-a-palavra-da-vida-em-meio-a-geracao`
   - Imagem: `feitos-para-brilhar-vivendo-a-palavra-da-vida-em-meio-a-geracao.png`
3. `Depois da festa: onde ficou Jesus?`
   - Slug: `depois-da-festa-onde-ficou-jesus`
   - Imagem: `depois-da-festa-onde-ficou-jesus.png`

## Páginas públicas

- `/index.html`: home.
- `/autor.html`: página pública do Pastor Antônio Lemos.
- `/sobre.html`: página sobre o projeto.
- `/contato.html`: página com formulário via e-mail e contato público `contato@verbovivo.blog`.
- `/faq.html`: perguntas frequentes.
- `/politica-de-privacidade.html`: política de privacidade em linguagem compatível com LGPD.
- `/sitemap.xml`, `/feed.xml`, `/robots.txt`, `/ads.txt`.

## Páginas ocultas/administrativas

- `/revisao.php?token=...`: abre rascunhos gerados por `artigo@verbovivo.blog`, permite corrigir e aprovar.
- `/gestor-artigos.php?token=...`: gestor escondido para editar/excluir artigos publicados.
- `/cron-diagnostico.php?token=...`: diagnóstico do cron, IMAP e logs.
- `/autorizar-remetente.php?token=...&mode=temporary|permanent`: autoriza remetente bloqueado.
- `/cron-editorial.php`: feito para CLI/Cron; pelo navegador deve retornar 403.
- `/_private/`: configuração privada no servidor, protegida por `.htaccess`.

## Segurança e autorização

- Credenciais locais ficam em `automation/.env`, ignorado pelo Git.
- Configuração privada do servidor fica em `_private/editorial-config.php`.
- O gestor e diagnóstico usam `admin_token`.
- Remetentes precisam estar autorizados para o agente processar e-mails.
- Remetente não autorizado gera e-mail para o aprovador com autorização temporária ou permanente.
- Nunca publicar chaves, senhas, `.env`, tokens, prints sensíveis ou conteúdo de `_private`.

## E-mails do projeto

- `contato@verbovivo.blog`: contato público.
- `artigo@verbovivo.blog`: recebe artigo bruto, refina, gera imagem e responde com preview/link de aprovação.
- `publicar@verbovivo.blog`: recebe artigo pronto com imagem e normaliza para o layout do site.

## Agentes e automação

- Agente Python local:
  - `python -m automation.editorial_agent.worker poll-once`
  - `python -m automation.editorial_agent.worker publish-once`
  - `python -m automation.editorial_agent.deploy_site`
  - `python -m automation.editorial_agent.upload_cron_config`
- Agente PHP no servidor:
  - `site/cron-editorial.php`
  - Roda por Cron Jobs da Hostinger.
  - Cron configurado para 10h e 22h.
- `artigo@` passa por aprovação humana.
- `publicar@` é caminho para artigo já pronto.

## Recursos implantados

- Artigos com narração via Web Speech API.
- Referências bíblicas devem ser expandidas para narração, exemplo: `Mateus, capítulo 21, versículo 17`.
- Ícone de áudio moderno com alto-falante, clique para ouvir/pausar.
- Redes sociais de autores com ícones oficiais e links embutidos.
- Página do autor Antônio Lemos com foto, bio e redes.
- Analytics próprio em `analytics.php`.
- Google Analytics e AdSense nos HTMLs principais.
- Search Console verificado por arquivo HTML.
- Sitemap e RSS gerados.

## Manutenções recentes importantes

- Removidos protótipos antigos, croquis e scripts que recriavam artigos descartados.
- Home restaurada para os três artigos atuais.
- Removidos artigos/imagens antigas do servidor.
- Corrigido `gestor-artigos.php`: o erro 500 era causado por BOM invisível antes de `<?php` e por compatibilidade PHP. Arquivos PHP foram regravados sem BOM.
- `gestor-artigos.php`, `revisao.php` e `cron-editorial.php` agora têm polyfills para funções modernas quando necessário.
- Último commit de correção do gestor: `d22ed68 Fix PHP manager compatibility`.

## Backups e relatórios

- Backup de manutenção profunda:
  - `C:\Users\Heber\Documents\BLOGs e SITES\Codex\backups\verbovivo-blog-2026-05-27_20-50-48`
- Relatório:
  - `C:\Users\Heber\Documents\BLOGs e SITES\Codex\relatorios\RELATORIO_MANUTENCAO_VERBOVIVO_2026-05-27.md`

## Checklist obrigatório antes de encerrar qualquer manutenção

1. Verificar `https://verbovivo.blog/`.
2. Verificar os três artigos atuais.
3. Verificar `sitemap.xml` e `feed.xml`.
4. Verificar `gestor-artigos.php?token=...`.
5. Verificar `revisao.php` com token válido quando houver rascunho.
6. Verificar `cron-diagnostico.php?token=...`.
7. Confirmar que `cron-editorial.php` retorna 403 no navegador.
8. Confirmar que `_private` não fica acessível publicamente.
9. Rodar `git status --short`.
10. Fazer commit e push se houver mudança versionável.

## Ideia salva para o futuro: ampliar o gestor

Não implementar agora. Apenas registrar para retomada futura.

Possíveis ampliações do `gestor-artigos.php`:

- Editar textos das páginas fixas: Home, Sobre, Autor, Contato, FAQ e Política de Privacidade.
- Trocar imagens dos artigos por upload.
- Editar foto e dados do autor.
- Gerenciar imagens não usadas.
- Ajustar SEO básico: title, description, canonical e og:image.
- Criar backups automáticos antes de qualquer salvamento.
- Histórico de alterações e botão de restaurar versão anterior.
- Adicionar senha além do token secreto.

Recomendação de implantação futura:

1. Primeiro: upload/troca de imagem de artigo.
2. Segundo: editor de páginas fixas.
3. Terceiro: gerenciador de imagens.
4. Quarto: histórico/backup/rollback.
5. Quinto: login/senha além do token.

## Prompt curto para retomar em uma conversa nova

Estou continuando o projeto `verbovivo.blog`. Leia primeiro `docs/MEMORIAL_COMPACTO_VERBOVIVO.md`, depois verifique `README.md`, `automation/README.md`, `commercial_agent/ROTEIRO_EBOOK_BETA.md` e o estado do Git. Não altere o gestor sem pedido explícito. Antes de qualquer limpeza, preserve páginas ocultas: `gestor-artigos.php`, `revisao.php`, `cron-diagnostico.php`, `autorizar-remetente.php` e `cron-editorial.php`.
