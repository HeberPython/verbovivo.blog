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
- Publicacao final.
- RSS, sitemap e Search Console.

Entrega do capitulo:

Diagrama do fluxo: autor -> e-mail -> agente -> revisao -> aprovacao -> site -> Google.

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

Entrega do capitulo:

Templates de envio e convite para autores.

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

Entrega do capitulo:

Checklist de publicacao e pos-publicacao.

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
- Backup antes de mudancas.
- O que nunca colocar em produto publico.

Entrega do capitulo:

Checklist de seguranca para lancamento.

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

## Anexos

Anexo A: Glossario simples.

Anexo B: Checklist dominio e hospedagem.

Anexo C: Checklist GitHub e estrutura.

Anexo D: Templates de e-mail editorial.

Anexo E: Checklist SEO.

Anexo F: Checklist de seguranca.

Anexo G: Planilha de metricas.

Anexo H: Custos externos possiveis.

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
