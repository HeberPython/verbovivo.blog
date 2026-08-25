# Auditoria AdSense e Qualidade Editorial - 25/08/2026

## Estado observado no AdSense

- Conta acessada pela sessão já autenticada do navegador interno do Codex.
- Site: `verbovivo.blog`.
- Status de aprovação: `Requer atenção`.
- Detalhe do status: `Conteúdo de baixo valor`.
- Status do `ads.txt` no painel: `Não encontrado`.
- Última atualização exibida pelo AdSense: `6 de agosto de 2026, 18:10 GMT-2`.

## Verificação pública do site

- `https://verbovivo.blog/ads.txt` responde HTTP 200.
- Conteúdo atual do `ads.txt`: `google.com, pub-5233928852442075, DIRECT, f08c47fec0942fa0`.
- O sitemap, RSS, página inicial, páginas institucionais, artigos e lições já existem e estão indexáveis no projeto.

## Riscos encontrados

- O painel do AdSense ainda não reprocessou o `ads.txt`, embora o arquivo esteja público.
- A Política de Privacidade estava desatualizada em relação ao uso real do site, pois ainda dizia que não havia formulário ativo e não citava claramente Analytics/AdSense.
- Havia caracteres quebrados no final da Política de Privacidade.
- A página `Comece aqui`, que organiza trilhas de leitura e fortalece a curadoria editorial, não estava presente na navegação principal de todas as páginas.

## Correções aplicadas

- Atualizada a Política de Privacidade para citar:
  - formulário de contato por e-mail;
  - dados técnicos de navegação;
  - Google Analytics;
  - Google AdSense;
  - cookies e tecnologias semelhantes;
  - canal oficial `contato@verbovivo.blog`;
  - data de atualização em 25 de agosto de 2026.
- Corrigido texto com caracteres quebrados na Política de Privacidade.
- Adicionado `Comece aqui` à navegação principal das páginas públicas.
- Adicionado `Comece aqui` aos templates usados pelo agente para novos artigos e novas lições.

## O que ainda depende do Google

- O AdSense precisa reprocessar o `ads.txt` e reavaliar o conteúdo.
- A aprovação por AdSense não é instantânea e pode continuar acusando baixo valor enquanto o Google não reconhecer volume, profundidade, navegação e sinais editoriais suficientes.

## Checklist antes de pedir nova revisão

- Confirmar que `https://verbovivo.blog/ads.txt` continua respondendo HTTP 200.
- Confirmar que a Política de Privacidade publicada está atualizada.
- Confirmar que a página `Comece aqui` está acessível pela navegação.
- Confirmar que as páginas `Sobre`, `Autor`, `Contato`, `FAQ` e `Privacidade` estão acessíveis.
- Confirmar que os artigos recentes continuam na home, sitemap e RSS.
- Evitar pedir revisão imediatamente após uma publicação técnica; aguardar o AdSense atualizar o estado do `ads.txt` quando possível.
