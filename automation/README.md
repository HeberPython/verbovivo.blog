# Automação editorial do Verbo Vivo

Este módulo prepara o fluxo de agente para novos artigos enviados por e-mail.

## Fluxos desejados

### Revisão com aprovação

1. Um artigo é enviado para `artigo@verbovivo.blog`.
2. O agente lê o e-mail e extrai o texto ou anexo.
3. O agente cria uma versão reflexiva, coerente e mais acessível do artigo.
4. O agente gera uma imagem condizente com o contexto bíblico e pastoral.
5. O agente envia uma resposta para aprovação.
6. O aprovador escolhe:
   - **Aprovar e publicar**
   - **Corrigir e publicar**
7. Após aprovação, o agente publica no site via FTP.

### Publicação direta

1. Um artigo já pronto é enviado para `publicar@verbovivo.blog`.
2. O agente lê o e-mail e extrai o texto ou anexo.
3. Se houver imagem anexada, ela é usada como capa.
4. O agente normaliza o HTML para manter o layout, cores, tipografia e aparência do Verbo Vivo.
5. O artigo é publicado diretamente no site via FTP, sem etapa de aprovação.

## O que falta configurar

As credenciais ficam fora do GitHub, em variáveis de ambiente:

```txt
EDITORIAL_IMAP_HOST=
EDITORIAL_IMAP_PORT=993
EDITORIAL_IMAP_USER=artigo@verbovivo.blog
EDITORIAL_IMAP_PASSWORD=

EDITORIAL_SMTP_HOST=
EDITORIAL_SMTP_PORT=465
EDITORIAL_SMTP_USER=artigo@verbovivo.blog
EDITORIAL_SMTP_PASSWORD=

PUBLISH_IMAP_HOST=imap.hostinger.com
PUBLISH_IMAP_PORT=993
PUBLISH_IMAP_USER=publicar@verbovivo.blog
PUBLISH_IMAP_PASSWORD=

EDITORIAL_APPROVAL_BASE_URL=
EDITORIAL_APPROVER_EMAIL=

HOSTINGER_FTP_HOST=ftp.verbovivo.blog
HOSTINGER_FTP_PORT=21
HOSTINGER_FTP_USER=u454442761.codex
HOSTINGER_FTP_PASSWORD=
HOSTINGER_FTP_DIR=/

OPENAI_API_KEY=
```

## Rodar localmente

```powershell
pip install -r automation/requirements.txt
python -m automation.editorial_agent.server
```

Em outro terminal:

```powershell
python -m automation.editorial_agent.worker poll-once
```

Para publicar mensagens prontas enviadas para `publicar@verbovivo.blog`:

```powershell
python -m automation.editorial_agent.worker publish-once
```

## Observação

Este agente precisa ficar rodando em algum ambiente persistente. Pode ser:

- um computador ligado;
- VPS;
- serviço de backend;
- automação futura no próprio ambiente Codex, quando configurarmos rotina recorrente.
