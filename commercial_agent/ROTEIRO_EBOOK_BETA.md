# Roteiro do Ebook Beta - Verbo Vivo Lab

Titulo:

**Verbo Vivo Lab: Blog Editorial Automatizado do Zero**

Subtitulo:

**Como construi o verbovivo.blog com dominio, hospedagem, GitHub, e-mails editoriais, agentes, aprovacao humana, publicacao automatica, SEO e seguranca.**

Formato recomendado para o beta:

- PDF de 45 a 70 paginas.
- Linguagem pratica, com screenshots e checklists.
- Um capitulo por decisao importante.
- Pouco codigo no corpo principal; detalhes tecnicos ficam em anexos.
- Incluir uma pagina de "Atualizacao da versao" sempre que o caso real do blog evoluir.

## Nota de atualizacao para a proxima versao do ebook

Esta versao do ebook precisa refletir as melhorias implantadas no `verbovivo.blog` depois da primeira configuracao:

- O blog passou a ter um gestor oculto de artigos publicados em `gestor-artigos.php`, protegido por token.
- O agente passou a bloquear remetentes nao autorizados antes de preparar/publicar artigos.
- Quando um remetente novo envia conteudo, o aprovador recebe link para autorizacao temporaria ou permanente.
- Foram criadas paginas ocultas de apoio: revisao, autorizacao de remetente, diagnostico do cron e gestor.
- O cron editorial roda na Hostinger em horarios programados e pode ser diagnosticado por pagina protegida.
- O site ganhou medicao propria anonima em `analytics.php`, alem de Google Analytics/Search Console/AdSense.
- Os artigos ganharam narração no navegador; referencias biblicas precisam ser escritas por extenso para nao serem lidas como horario.
- A manutencao profunda removeu prototipos antigos, scripts obsoletos e referencias a artigos descartados.
- Foi identificado um erro real de producao: arquivos PHP com BOM invisivel antes de `<?php` quebraram paginas com `declare(strict_types=1)`. O caso deve entrar como alerta pratico no capitulo de manutencao.
- O gestor oculto deve ser citado como recurso existente, mas a ampliacao para editar paginas fixas e imagens deve ficar como possibilidade futura, nao como promessa do beta.

## Introducao - O que voce esta prestes a construir

Objetivo:

Mostrar que o produto nao e sobre "ficar rico com blog", mas sobre criar uma estrutura editorial propria, com processo e independencia.

Conteudo:

- A historia curta do `verbovivo.blog`.
- O problema do blog parado.
- A diferenca entre publicar conteudo e operar um sistema editorial.
- O que este ebook entrega e o que nao entrega.

Exercicio:

Escreva em uma frase qual sera a funcao do seu blog.

## Capitulo 1 - A ideia antes da ferramenta

Objetivo:

Definir nicho, linha editorial e criterio de publicacao antes de escolher tecnologia.

Conteudo:

- Publico.
- Promessa editorial.
- Categorias iniciais.
- Tipos de artigo.
- Frequencia realista.
- Por que um blog proprio complementa redes sociais.

Entrega do capitulo:

Mapa simples da linha editorial.

## Capitulo 2 - O mapa do sistema

Objetivo:

Apresentar a arquitetura do Verbo Vivo de forma visual e compreensivel.

Conteudo:

- Dominio.
- Hospedagem.
- Repositorio.
- Site estatico.
- E-mails editoriais.
- Agente local/PHP.
- Aprovacao por token.
- Gestor oculto por token para manutencao pontual de artigos.
- Paginas ocultas de apoio: revisao, autorizacao, diagnostico e gestor.
- Publicacao final.
- RSS, sitemap e Search Console.

Entrega do capitulo:

Diagrama do fluxo: autor -> e-mail -> agente -> revisao -> aprovacao -> site -> Google.

Atualizacao sugerida do diagrama:

autor autorizado -> e-mail editorial -> agente -> preview por e-mail -> revisao por token -> publicacao -> home/feed/sitemap -> Search Console.

Fluxo de excecao:

remetente novo -> agente bloqueia -> e-mail ao aprovador -> autorizacao temporaria/permanente -> processamento no proximo ciclo.

## Capitulo 3 - Dominio, hospedagem e presenca propria

Objetivo:

Explicar as decisoes de infraestrutura sem transformar o ebook em manual tecnico pesado.

Conteudo:

- Por que dominio proprio importa.
- O papel da Hostinger no projeto.
- Hospedagem, FTP, e-mails e Cron Jobs.
- O que precisa ser contratado.
- Custos externos e cuidados antes de comprar.

Entrega do capitulo:

Checklist de dominio e hospedagem.

## Capitulo 4 - GitHub, arquivos e site estatico

Objetivo:

Mostrar como o blog pode existir sem WordPress.

Conteudo:

- O que e um site estatico.
- Estrutura basica: home, artigos, imagens, paginas institucionais.
- Repositorio como historico do projeto.
- GitHub como organizacao e backup de codigo.
- Vercel como possibilidade de preview/deploy.
- Hostinger como publicacao final do caso real.

Entrega do capitulo:

Checklist de estrutura inicial de arquivos.

## Capitulo 5 - E-mails editoriais

Objetivo:

Mostrar como o e-mail vira interface simples para alimentar o blog.

Conteudo:

- `contato@`: e-mail publico.
- `artigo@`: entrada para revisao e aprovacao.
- `publicar@`: entrada para publicacao direta.
- Como separar e-mails evita confusao operacional.
- Modelo de envio para autores.
- Como anexos e imagens entram no fluxo.
- Lista de remetentes autorizados.
- O que acontece quando alguem fora da lista tenta enviar artigo.
- Autorizacao temporaria versus autorizacao permanente.

Entrega do capitulo:

Templates de envio e convite para autores.

Acrescimo necessario:

Explicar que `artigo@` e `publicar@` nao devem aceitar qualquer remetente. O caso real passou a exigir allowlist manual. Isso evita que compradores do ebook, curiosos ou terceiros consigam acionar o fluxo editorial apenas descobrindo os enderecos.

## Capitulo 6 - Agentes com supervisao humana

Objetivo:

Explicar o papel dos agentes sem vender automacao cega.

Conteudo:

- O agente como assistente editorial, nao como dono da voz.
- Refino de texto.
- Geracao de resumo, tags, categoria e metadados.
- Geracao ou uso de imagem.
- Quando usar IA e quando publicar sem IA.
- Como preservar a voz do autor.
- Diferenca entre o fluxo com IA (`artigo@`) e o fluxo de formatacao/publicacao direta (`publicar@`).
- Por que o fluxo direto deve apenas normalizar layout, tipografia, imagem e estrutura, sem reescrever desnecessariamente.

Entrega do capitulo:

Checklist de decisao: IA necessaria ou publicacao direta?

## Capitulo 7 - Aprovacao humana antes de publicar

Objetivo:

Mostrar o ponto de confianca do sistema.

Conteudo:

- Por que aprovacao humana e essencial.
- Link/token de revisao.
- Botao de aprovar e publicar.
- Correcao antes da publicacao.
- Evitar publicacao indevida.
- Como transformar revisao em rotina simples.
- Preview no proprio e-mail antes de abrir a revisao.
- Link de correcao quando for preciso alterar o artigo.
- Relacao entre revisao por token e seguranca operacional.

Entrega do capitulo:

Checklist de aprovacao.

## Capitulo 8 - Publicacao automatica e manutencao

Objetivo:

Explicar o que acontece depois do clique de aprovacao.

Conteudo:

- Criacao da pagina do artigo.
- Atualizacao da home.
- Atualizacao do feed RSS.
- Atualizacao do sitemap.
- Envio para hospedagem.
- Rotinas manuais e rotinas agendadas.
- O papel do Cron Jobs na Hostinger.
- Diagnostico do cron por pagina protegida.
- Log do cron em pasta privada.
- Manutencao profunda: backup, limpeza de arquivos obsoletos, testes e rollback.
- Cuidado com compatibilidade PHP na hospedagem.

Entrega do capitulo:

Checklist de publicacao e pos-publicacao.

Estudo de caso para inserir:

Durante a manutencao do `verbovivo.blog`, o gestor oculto retornou erro 500. O arquivo existia, mas um caractere invisivel BOM antes de `<?php` quebrou o PHP porque o arquivo usava `declare(strict_types=1)`. A solucao foi regravar os PHPs sem BOM, testar o link protegido e criar a regra: toda manutencao deve validar tambem paginas ocultas, nao apenas a home publica.

## Capitulo 9 - SEO simples para nao publicar no escuro

Objetivo:

Ensinar o basico que sustenta descoberta organica.

Conteudo:

- Titulo.
- Slug.
- Meta description.
- Alt text.
- Links internos.
- Sitemap.
- RSS.
- Robots.txt.
- Search Console.
- O que acompanhar depois da publicacao.
- Google Analytics.
- Medicao propria simples em `analytics.php`.
- AdSense quando o projeto estiver maduro.

Entrega do capitulo:

Checklist SEO de artigo.

## Capitulo 10 - Seguranca operacional

Objetivo:

Evitar que o comprador replique o sistema de forma insegura.

Conteudo:

- Credenciais fora do GitHub.
- Variaveis de ambiente.
- Pasta privada no servidor.
- Remetentes autorizados.
- Bloqueio de e-mails de servico.
- Revisao por token.
- Gestor oculto por token.
- Diagnostico protegido por token.
- Autorizacao temporaria/permanente de remetente.
- Arquivos PHP sem BOM.
- Compatibilidade com versoes PHP da hospedagem.
- Backup antes de mudancas.
- O que nunca colocar em produto publico.

Entrega do capitulo:

Checklist de seguranca para lancamento.

Checklist complementar de seguranca:

- Testar `_private` retornando acesso negado.
- Testar `cron-editorial.php` retornando 403 pelo navegador.
- Testar `gestor-artigos.php` com token valido.
- Testar `gestor-artigos.php` sem token retornando 404.
- Verificar se nenhum arquivo `.env`, token OAuth, chave OpenAI ou senha foi para o GitHub.
- Validar que remetente nao autorizado nao publica artigo.
- Confirmar que o aprovador recebe e-mail de autorizacao.

## Capitulo 11 - Como adaptar para seu nicho

Objetivo:

Fazer a ponte entre o Verbo Vivo e o projeto do comprador.

Conteudo:

- Blog autoral.
- Blog de igreja ou ministerio.
- Blog de pequenos negocios.
- Blog de autoridade profissional.
- Blog para clientes.
- O que muda e o que permanece.

Entrega do capitulo:

Plano de adaptacao em uma pagina.

## Capitulo 12 - Seu plano de 7 dias

Objetivo:

Fechar com acao simples.

Conteudo:

Dia 1: definir proposta editorial.

Dia 2: escolher dominio e estrutura.

Dia 3: organizar paginas essenciais.

Dia 4: configurar e-mails.

Dia 5: desenhar fluxo de revisao.

Dia 6: publicar primeiro artigo.

Dia 7: revisar SEO, seguranca e rotina.

Entrega do capitulo:

Checklist final de execucao.

Atualizacao sugerida do Dia 7:

Incluir uma revisao obrigatoria das paginas ocultas:

- `revisao.php`
- `gestor-artigos.php`
- `cron-diagnostico.php`
- `autorizar-remetente.php`
- `cron-editorial.php`

Essa etapa ensina que um projeto editorial automatizado nao e apenas a parte bonita da home; os bastidores precisam estar saudaveis.

## Anexos

Anexo A: Glossario simples.

Anexo B: Checklist dominio e hospedagem.

Anexo C: Checklist GitHub e estrutura.

Anexo D: Templates de e-mail editorial.

Anexo E: Checklist SEO.

Anexo F: Checklist de seguranca.

Anexo G: Planilha de metricas.

Anexo H: Custos externos possiveis.

Anexo I: Checklist de manutencao e rollback.

Anexo J: Gabarito de teste das paginas ocultas.

Anexo K: Backlog do gestor oculto.

## Anexo I - Checklist de manutencao e rollback

- Fazer backup antes de limpar arquivos.
- Conferir `git status`.
- Verificar home, artigos, imagens, `sitemap.xml` e `feed.xml`.
- Verificar paginas ocultas com token.
- Remover arquivos obsoletos somente depois de confirmar que nao participam do fluxo vivo.
- Publicar na Hostinger.
- Testar online com HTTP 200/403/404 esperados.
- Fazer commit e push.
- Registrar relatorio de manutencao.

## Anexo J - Gabarito de teste das paginas ocultas

- `gestor-artigos.php?token=...`: deve abrir com token valido.
- `gestor-artigos.php`: deve esconder a pagina.
- `revisao.php?token=...`: deve abrir quando houver rascunho valido.
- `cron-diagnostico.php?token=...`: deve mostrar IMAP/logs com token valido.
- `cron-editorial.php`: deve retornar 403 no navegador.
- `_private/`: deve ficar inacessivel publicamente.
- `autorizar-remetente.php?token=...`: deve processar apenas token valido.

## Anexo K - Backlog do gestor oculto

O caso real possui um gestor simples para artigos. Futuramente, ele pode evoluir para:

- Trocar imagem de capa por upload.
- Editar paginas fixas.
- Editar dados do autor.
- Gerenciar biblioteca de imagens.
- Ajustar SEO basico.
- Criar backup automatico antes de salvar.
- Manter historico e restaurar versoes.
- Exigir senha alem do token.

No beta, apresentar isso como possibilidade de evolucao, nao como recurso prometido.

## Pagina complementar

Criar uma pagina simples para compradores com:

- Boas-vindas.
- Download do PDF.
- Downloads dos templates.
- Links uteis.
- Atualizacoes e erratas.
- FAQ vivo com duvidas do beta.
- Aviso claro: nao publicar credenciais, senhas ou dados sensiveis.

Nome sugerido:

**Central do Comprador - Verbo Vivo Lab**
