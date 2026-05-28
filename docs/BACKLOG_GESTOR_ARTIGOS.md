# Backlog do gestor oculto

Status: ideia registrada, sem implementação agora.

## Objetivo futuro

Transformar `gestor-artigos.php` em um painel administrativo mais completo para pequenas alterações editoriais no `verbovivo.blog`, sem precisar acionar o Codex para ajustes simples.

## O que já existe

O gestor oculto atual permite:

- Listar artigos publicados.
- Editar título, slug, categoria, resumo, autor, imagem indicada e HTML do corpo.
- Excluir artigo publicado.
- Atualizar índices relacionados ao artigo.
- Acessar somente por link com token secreto.

## Possibilidades futuras

- Upload e troca de imagem de capa dos artigos.
- Editor de páginas fixas:
  - Home.
  - Sobre.
  - Autor.
  - Contato.
  - FAQ.
  - Política de Privacidade.
- Editor da página do autor:
  - Nome.
  - Bio.
  - Foto.
  - Redes sociais.
  - Mensagem aos leitores.
- Gerenciador de imagens:
  - Enviar imagem.
  - Listar imagens.
  - Identificar imagens não usadas.
  - Excluir imagens não usadas.
- SEO básico:
  - `title`.
  - `description`.
  - `canonical`.
  - `og:image`.
- Backup automático antes de salvar.
- Histórico de alterações.
- Restaurar versão anterior.
- Segundo fator simples: senha além do token.

## Ordem recomendada se for retomado

1. Upload/troca de imagem dos artigos.
2. Backup automático antes de salvar.
3. Editor de páginas fixas.
4. Editor de autor.
5. Gerenciador de imagens.
6. Histórico/rollback.
7. Senha adicional além do token.

## Cuidados

- Não remover o token atual.
- Não deixar rota administrativa linkada no menu público.
- Não salvar credenciais no HTML.
- Não permitir upload sem validar extensão e tamanho.
- Não apagar imagens sem verificar uso em artigos, home e metatags.
- Testar sempre no servidor da Hostinger, porque PHP local pode não existir no computador.
