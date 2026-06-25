# Estudo de viabilidade: comentarios nos artigos do Verbo Vivo

Data: 25/06/2026

## Objetivo

Adicionar comentarios aos artigos do Verbo Vivo sem transformar o blog em uma rede social dificil de moderar. O ideal e permitir que leitores identificados comentem, que o autor/responsavel consiga responder, e que haja notificacao por e-mail, Telegram ou painel quando chegar comentario novo.

## Resumo executivo

A opcao mais equilibrada para o Verbo Vivo e usar comentarios baseados em GitHub Discussions com giscus.

Motivos:

- Nao exige banco de dados proprio.
- Nao exige manter servidor extra.
- E gratuito, sem anuncios e sem rastreamento.
- Cada artigo pode virar uma discussao propria.
- Os comentarios aparecem dentro do artigo.
- A moderacao acontece no GitHub.
- Exige login do GitHub, reduzindo anonimato e spam.

O ponto fraco e que nem todo leitor comum tem conta no GitHub. Para um publico cristao amplo, isso pode diminuir a quantidade de comentarios.

A segunda opcao mais interessante e um sistema proprio simples com formulario, aprovacao e notificacao por e-mail/Telegram. Da mais controle e permite login por Google no futuro, mas exige banco de dados e mais manutencao.

Discord e viavel como comunidade paralela, mas nao e a melhor opcao para comentarios embutidos em blog. Ele funciona melhor como "grupo da comunidade" do que como caixa de comentarios por artigo.

## Opcoes avaliadas

### 1. giscus + GitHub Discussions

Como funciona:

- O blog carrega um widget de comentarios.
- O giscus procura uma Discussion do GitHub associada ao artigo pelo caminho da pagina, titulo ou URL.
- Se nao existir, ele cria uma discussao quando alguem comenta.
- O leitor precisa autorizar o giscus pelo login do GitHub.
- Os comentarios ficam salvos no GitHub Discussions e aparecem no artigo.

Pontos fortes:

- Gratuito.
- Sem banco de dados.
- Sem anuncios.
- Sem rastreamento.
- Moderacao pelo GitHub.
- Bom para site estatico.
- Permite reacoes.
- Cada artigo pode ter sua propria conversa.

Pontos fracos:

- Exige conta GitHub.
- Pode ser menos amigavel para leitores que nao sao tecnicos.
- A moderacao depende do ambiente do GitHub.

Viabilidade tecnica para o Verbo Vivo:

Alta. O blog ja esta no GitHub e e estatico. Basta ativar GitHub Discussions no repositorio, instalar/configurar o giscus e incluir o script no template dos artigos.

Minha avaliacao:

Melhor opcao para primeiro teste. E simples, segura e reversivel.

## 2. Utterances + GitHub Issues

Como funciona:

- Similar ao giscus, mas usa GitHub Issues em vez de GitHub Discussions.
- Cada artigo vira uma Issue.
- O leitor comenta com login GitHub.

Pontos fortes:

- Gratuito.
- Sem banco.
- Sem anuncios.
- Leve.

Pontos fracos:

- Issues parecem mais tecnicas e menos adequadas para conversas editoriais.
- GitHub Discussions combina melhor com comentarios e comunidade.

Viabilidade tecnica:

Alta, mas inferior ao giscus para este blog.

Minha avaliacao:

Nao recomendo como primeira escolha, porque Discussions e mais natural para conversas.

## 3. Sistema proprio com formulario e moderacao

Como funcionaria:

- Cada artigo teria um botao "Comentar".
- O leitor preencheria nome, e-mail e comentario.
- Opcionalmente, login Google poderia ser adicionado depois.
- O comentario iria para uma fila de aprovacao.
- O administrador receberia aviso por e-mail ou Telegram.
- Apos aprovacao, o comentario apareceria no artigo.
- O autor/responsavel poderia responder.

Pontos fortes:

- Mais amigavel ao leitor comum.
- Nao exige GitHub.
- Podemos exigir nome e e-mail.
- Podemos moderar tudo antes de publicar.
- Podemos guardar historico de comentarios e respostas.
- Pode evoluir para login Google.

Pontos fracos:

- Exige banco de dados.
- Exige backend/API.
- Exige protecao contra spam.
- Exige LGPD mais cuidadosa, porque coletaria nome/e-mail/IP.
- Exige tela administrativa.

Banco possivel:

- Supabase: boa opcao, porque o usuario ja tem conta e ele suporta Auth, banco e APIs.
- Firebase: bom para login Google, mas pode ficar mais acoplado ao ecossistema Google.
- Hostinger/MySQL: possivel, mas menos confortavel para automacao moderna.

Viabilidade tecnica:

Media/alta. E a melhor opcao se o objetivo for comentarios realmente populares entre leitores comuns, mas deve ser feita com cuidado.

Minha avaliacao:

Boa opcao para segunda fase, depois de testar se os leitores realmente comentam.

## 4. Discord como plataforma de comentarios

Ideia:

- Cada artigo publicado criaria automaticamente um topico/thread no Discord.
- No artigo apareceria um botao "Comentar no Discord".
- O leitor clicaria, entraria no canal/topico do artigo e comentaria.
- O blog poderia exibir alguns comentarios do Discord usando API/bot.

Pontos fortes:

- Excelente para comunidade recorrente.
- Bom para conversas longas.
- Permite moderadores, cargos, regras e notificacoes.
- Pode aproximar leitores em um ambiente comunitario.

Pontos fracos:

- Leitor precisa ter Discord.
- Comentario sai do fluxo natural do artigo.
- Embutir comentarios do Discord no blog exige bot, API e cuidado com permissao.
- Pode distrair do blog e levar a conversa para fora do site.
- Exige moderacao ativa.

Viabilidade tecnica:

Media. A API do Discord permite criar canais, threads e mensagens, e Forum Channels funcionam como topicos. Mas transformar isso em comentarios embutidos bonitos e confiaveis no blog exige mais engenharia.

Minha avaliacao:

Bom como comunidade paralela do Verbo Vivo, nao como primeira caixa de comentarios.

## 5. Disqus, Hyvor Talk e plataformas prontas

Como funcionam:

- Voce cria uma conta no servico.
- Cola um script no site.
- O servico cuida de login, comentario, moderacao e notificacoes.

Pontos fortes:

- Rapido para instalar.
- Painel de moderacao pronto.
- Notificacoes prontas.
- Mais familiar para leitores comuns.

Pontos fracos:

- Dependencia de terceiro.
- Pode ter custo.
- Pode ter anuncios, rastreamento ou impacto de privacidade.
- Pode pesar no carregamento do site.
- Exige rever Politica de Privacidade/LGPD.

Viabilidade tecnica:

Alta, mas com custo reputacional/privacidade maior.

Minha avaliacao:

Eu nao usaria como primeira opcao no Verbo Vivo, porque o blog busca sobriedade, leveza e confianca.

## Recomendacao por fases

### Fase 1: teste controlado com giscus

Implementar comentarios em 3 a 5 artigos mais fortes.

Regras:

- Comentarios exigem login GitHub.
- Comentarios aparecem no fim do artigo.
- Titulo da area: "Participe da reflexao".
- Texto curto: "Comente com respeito e edifique a conversa."
- Moderacao pelo GitHub Discussions.

Vantagem: custo quase zero e risco baixo.

### Fase 2: medir engajamento

Metricas importantes:

- Comentarios por artigo.
- Quantidade de pessoas diferentes comentando.
- Tempo medio na pagina antes/depois dos comentarios.
- Cliques em "comentar".
- Retorno de leitores ao mesmo artigo.
- Comentarios aprovados x comentarios removidos.
- Artigos que geram conversa saudavel.

Meta inicial realista:

- 1 a 3 comentarios por artigo em textos enviados diretamente a leitores conhecidos.
- 5% a 10% de clique em "comentar" entre leitores engajados.

### Fase 3: decidir se vale sistema proprio

Se leitores comuns tiverem dificuldade com GitHub, criar sistema proprio:

- Login Google ou formulario com nome/e-mail.
- Fila de aprovacao.
- Notificacao por Telegram/e-mail.
- Respostas do autor.
- Politica de comentarios.
- Registro de consentimento LGPD.

## Como ficaria no artigo

No fim do texto:

```txt
Participe da reflexao

Este espaco e para comentarios respeitosos, perguntas sinceras e testemunhos relacionados ao tema do artigo.

[Comentar]
```

Se for giscus, a caixa aparece ali mesmo.

Se for Discord, o botao abre o topico daquele artigo no Discord.

Se for sistema proprio, abre um formulario simples dentro do site.

## Politica minima de comentarios

Regras sugeridas:

- Comentarios devem dialogar com o tema do artigo.
- Discordancias sao permitidas, ofensas nao.
- Nao publicar dados pessoais de terceiros.
- Nao usar o espaco para propaganda.
- Comentarios podem ser removidos/moderados.
- Nome publico pode aparecer junto ao comentario.
- E-mail, se coletado, nao sera exibido.

## Impacto LGPD

Com giscus:

- O comentario e gerido pelo GitHub.
- O leitor usa conta GitHub.
- A Politica de Privacidade deve mencionar que comentarios usam GitHub Discussions/giscus.

Com sistema proprio:

- O Verbo Vivo passa a armazenar nome, e-mail, comentario, data e possivelmente IP.
- Precisa informar finalidade, base legal, retencao, remocao e canal de contato.
- Precisa permitir exclusao/correcao quando solicitado.

Com Discord:

- O comentario fica no Discord.
- A Politica de Privacidade deve informar redirecionamento para plataforma de terceiro.

## Decisao recomendada

Implementar primeiro giscus, com GitHub Discussions, em modo discreto e elegante.

Depois de 30 dias:

- Se houver comentarios saudaveis, manter e expandir.
- Se houver pouca adesao por causa do login GitHub, migrar para formulario proprio com Supabase e login Google.
- Se nascer uma comunidade recorrente, criar Discord separado, mas nao substituir a caixa de comentarios por Discord.

## Fontes consultadas

- giscus: https://giscus.app/
- utterances: https://utteranc.es/
- Discord Channels API: https://docs.discord.com/developers/resources/channel
- Discord Forum Channels FAQ: https://support.discord.com/hc/en-us/articles/6208479917079-Forum-Channels-FAQ
- Discord Webhooks: https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks
- google-github-actions/auth: https://github.com/google-github-actions/auth
- Google Cloud Workload Identity Federation: https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines
