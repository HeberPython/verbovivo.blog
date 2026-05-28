# Atualizacao para subir na Hotmart - 2026-05-28

Produto: **Verbo Vivo Lab: Blog Editorial Automatizado do Zero**

## Resumo para compradores

O material foi atualizado com melhorias reais feitas no `verbovivo.blog` depois da primeira montagem do sistema. A nova versao reforca seguranca, manutencao e bastidores operacionais do blog.

## O que entrou na atualizacao

- Lista de remetentes autorizados para impedir que qualquer pessoa acione os agentes por e-mail.
- Fluxo de autorizacao temporaria ou permanente para remetentes novos.
- Explicacao das paginas ocultas:
  - `gestor-artigos.php`
  - `revisao.php`
  - `cron-diagnostico.php`
  - `autorizar-remetente.php`
  - `cron-editorial.php`
- Checklist para testar paginas ocultas antes de encerrar manutencoes.
- Diferenca entre `artigo@verbovivo.blog` e `publicar@verbovivo.blog`.
- Atualizacao sobre o agente PHP rodando via Cron Jobs da Hostinger.
- Inclusao da medicao propria anonima em `analytics.php`.
- Inclusao de Google Analytics, Search Console e AdSense como camadas de acompanhamento.
- Licao real de manutencao: erro 500 causado por BOM invisivel antes de `<?php` em arquivo PHP.
- Backlog do gestor oculto, deixando claro que ampliacoes futuras sao possibilidade, nao recurso prometido no beta.

## Arquivos alterados

- `commercial_agent/ROTEIRO_EBOOK_BETA.md`
- `commercial_agent/PAGINA_COMPLEMENTAR_BETA.md`
- `commercial_agent/HOTMART_PASSO_A_PASSO.md`
- `docs/MEMORIAL_COMPACTO_VERBOVIVO.md`
- `docs/MEMORIAL_COMPACTO_VERBOVIVO.txt`
- `docs/BACKLOG_GESTOR_ARTIGOS.md`

## Texto curto para aviso na Hotmart

Atualizacao do material: adicionamos uma secao sobre seguranca por remetentes autorizados, paginas ocultas de gestao/revisao/diagnostico, checklist de manutencao, medicao propria do site e uma licao pratica sobre erro 500 em PHP causado por caractere invisivel no arquivo. A atualizacao tambem esclarece que a ampliacao do gestor oculto e uma possibilidade futura, nao uma promessa do beta atual.

## Checklist antes de subir

- Revisar o PDF final gerado a partir de `ROTEIRO_EBOOK_BETA.md`.
- Atualizar a pagina complementar com a nova secao "Atualizacoes do caso real".
- Enviar este changelog como nota de atualizacao, se a Hotmart permitir.
- Conferir se nenhuma credencial, token, senha ou print sensivel entrou no material.
- Conferir se o gestor oculto ampliado nao esta sendo vendido como recurso pronto.
