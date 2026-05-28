# Automacao editorial do Verbo Vivo

Este modulo prepara o fluxo de agente para novos artigos enviados por e-mail.

## Fluxos

### Revisao com aprovacao

1. Um artigo e enviado para `artigo@verbovivo.blog`.
2. O agente le o e-mail e extrai o texto ou anexo.
3. O agente cria uma versao reflexiva, coerente e mais acessivel do artigo.
4. O agente gera uma imagem condizente com o contexto biblico e pastoral.
5. O agente envia uma resposta com link de revisao em `verbovivo.blog`.
6. O aprovador escolhe `Aprovar e publicar` ou ajusta o texto em `Corrigir e publicar`.
7. A pagina de revisao publica no site e atualiza home, RSS e sitemap.

### Publicacao direta

1. Um artigo ja pronto e enviado para `publicar@verbovivo.blog`.
2. O agente le o e-mail e extrai o texto ou anexo.
3. Se houver imagem anexada, ela e usada como capa.
4. O agente normaliza o HTML para manter layout, cores, tipografia e aparencia do Verbo Vivo.
5. O artigo e publicado diretamente no site via FTP, sem etapa de aprovacao.

## Variaveis

As credenciais ficam fora do GitHub, em variaveis de ambiente:

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

EDITORIAL_APPROVAL_BASE_URL=https://verbovivo.blog
EDITORIAL_APPROVER_EMAIL=

HOSTINGER_FTP_HOST=ftp.verbovivo.blog
HOSTINGER_FTP_PORT=21
HOSTINGER_FTP_USER=u454442761.codex
HOSTINGER_FTP_PASSWORD=
HOSTINGER_FTP_DIR=/

OPENAI_API_KEY=

GA4_MEASUREMENT_ID=
GSC_SITE_URL=https://verbovivo.blog/
GOOGLE_APPLICATION_CREDENTIALS=
GSC_OAUTH_CLIENT_SECRETS=
GSC_OAUTH_TOKEN=
GOOGLE_ADSENSE_CLIENT=
HOSTINGER_ACCESS_LOG_PATH=automation/_logs/hostinger
HOSTINGER_ANALYTICS_REMOTE_LOG=_private/analytics-events.jsonl
HOSTINGER_ANALYTICS_LOCAL_LOG=automation/_logs/hostinger/first-party-analytics.jsonl

TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
TELEGRAM_GH_REPO=
TELEGRAM_GH_WORKFLOW=
GITHUB_TOKEN_FOR_TELEGRAM=
```

## Comandos

Instalar dependencias:

```powershell
pip install -r automation/requirements.txt
```

Ler `artigo@verbovivo.blog`, preparar rascunho, gerar imagem e enviar link de revisao:

```powershell
python -m automation.editorial_agent.worker poll-once
```

Publicar mensagens prontas enviadas para `publicar@verbovivo.blog`:

```powershell
python -m automation.editorial_agent.worker publish-once
```

Reenviar o site estatico completo para a Hostinger:

```powershell
python -m automation.editorial_agent.deploy_site
```

Gerar relatorio editorial/audiencia com as fontes configuradas:

```powershell
python -m automation.editorial_agent.audience_report
```

Autorizar o Search Console por OAuth, quando a conta de servico nao puder ser adicionada no Search Console:

```powershell
python -m automation.editorial_agent.audience_report --authorize-search-console
```

Enviar o resumo curto para o Telegram, quando `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` estiverem configurados:

```powershell
python -m automation.editorial_agent.audience_report --telegram
```

Tambem e possivel enviar pelo GitHub Actions reutilizando secrets existentes:

```txt
TELEGRAM_GH_REPO=HeberPython/agente-sites
TELEGRAM_GH_WORKFLOW=send_telegram.yml
GITHUB_TOKEN_FOR_TELEGRAM=<token com permissao para actions:write no repo>
```

Para ativar a tag do Google Analytics no HTML, configure `GA4_MEASUREMENT_ID` antes de rodar `scripts/build_static_site.py`. Para AdSense, configure `GOOGLE_ADSENSE_CLIENT`.

Para incluir logs da Hostinger, exporte/baixe os arquivos de acesso ou estatisticas do hPanel e coloque em `automation/_logs/hostinger`. O relatorio le arquivos `.log`, `.txt` e `.gz` dentro dessa pasta.

O site tambem possui uma medicao editorial propria em `analytics.php`, que salva eventos anonimizados em `_private/analytics-events.jsonl`. O relatorio tenta baixar esse arquivo via FTP antes de analisar.

## Observacao

O agente precisa rodar em algum ambiente persistente para verificar e-mails automaticamente. Por enquanto, ele pode ser executado sob demanda pelo Codex ou por um computador ligado. Depois, pode ser colocado em uma VPS ou rotina agendada.
