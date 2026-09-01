# Mural de Protecao do Verbo Vivo

Estas regras sao obrigatorias em qualquer manutencao deste projeto.

1. Nunca publicar `site/index.html`, `site/feed.xml` ou `site/sitemap.xml` diretamente sobre a Hostinger sem antes sincronizar o catalogo real de `public_html/artigos`.
2. A Hostinger e os rascunhos remotos aprovados contêm publicacoes que podem ainda nao existir no checkout do GitHub.
3. Antes de qualquer implantacao, criar inventario somente leitura e comparar:
   - paginas fisicas em `artigos/`;
   - links na home;
   - links no acervo completo `artigos.html`;
   - itens do feed;
   - URLs do sitemap;
   - rascunhos aprovados.
4. Antes de qualquer intervencao que possa alterar o site publicado, criar backup remoto do estado atual e guardar o artefato fora do deploy. Sem backup confirmado, nao implantar.
5. A home deve exibir somente os 3 artigos mais recentes: 1 destaque e 2 cards. Os demais artigos devem continuar acessiveis pelo link superior `Artigos`, no acervo completo `artigos.html`.
6. Uma implantacao deve falhar se qualquer artigo fisico ficar ausente de `artigos.html`, do feed ou do sitemap.
7. Nunca reduzir a quantidade de artigos publicados sem pedido explicito do usuario e backup anterior.
8. Mudancas pontuais de layout, imagem, texto, SEO ou automacao nao podem reconstruir o site a partir de uma copia local desatualizada.
9. Nao apagar imagens ou paginas orfas antes de confirmar se pertencem a uma publicacao aprovada.
10. Depois de toda manutencao, validar ao vivo:
   - status HTTP dos artigos recentes;
   - imagens dos artigos recentes;
   - quantidade de artigos na home;
   - quantidade de artigos em `artigos.html`;
   - unicidade dos itens do feed;
   - correspondencia entre artigos, feed e sitemap.
11. O ultimo artigo por data de publicacao fica em destaque, salvo excecao explicitamente registrada pelo usuario.
12. Se uma verificacao falhar, interromper a implantacao. Nao tentar “corrigir por cima”.
13. Recursos presentes em todas as paginas de artigo devem ser mantidos nos tres caminhos de geracao: template Python, aprovacao em `revisao.php` e edicao em `gestor-artigos.php`.

Comandos seguros no GitHub Actions:

- `audit-content`: auditoria somente leitura.
- `backup-content`: backup remoto completo antes de alteracoes no site publicado.
- `repair-content`: sincroniza o catalogo remoto, reconstrói os indices, valida e implanta.
- `test-image`: testa o Gemini sem ler e-mails.

Registro do incidente de 27/06/2026:

- Causa: uma manutencao enviou indices formados por uma copia local incompleta.
- Efeito: artigos recentes continuaram fisicamente no servidor, mas desapareceram da home.
- Prevencao: catalogo remoto obrigatorio e validacao de cobertura antes de toda implantacao.
