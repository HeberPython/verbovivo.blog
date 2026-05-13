from __future__ import annotations

import html
import shutil
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
ARTICLE_DIR = SITE / "artigos"
IMAGE_OUT = SITE / "images" / "articles"
IMAGE_IN = ROOT / "public" / "images" / "articles"
DOMAIN = "https://verbovivo-blog.vercel.app"


ARTICLES = [
    {
        "title": "Depois da Festa: onde ficou Jesus?",
        "slug": "depois-da-festa-onde-ficou-jesus",
        "category": "Vida Cristã",
        "date": "2026-05-10",
        "author": "Pastor Antonio Lemos Filho",
        "image": "depois-da-festa.png",
        "alt": "Rua antiga vazia ao anoitecer com ramos no chão e uma casa iluminada ao fundo",
        "excerpt": "Uma reflexão sobre acolher Jesus depois que os aplausos terminam e a vida comum recomeça.",
        "quote": "E, deixando-os, saiu da cidade para Betânia, e ali passou a noite. Mateus 21:17",
        "sections": [
            (
                "Quando os aplausos passam",
                [
                    "Há momentos em que a fé parece fácil. O ambiente ajuda, a música conduz, a comunhão aquece o coração e as palavras de adoração saem quase naturalmente. Mas a pergunta que permanece depois da celebração é simples e profunda: onde Jesus fica quando a festa acaba?",
                    "Mateus registra que, depois de ser aclamado, Jesus saiu de Jerusalém e passou a noite em Betânia. A cidade que o recebeu com ramos não lhe ofereceu morada. A multidão o celebrou, mas poucos o acolheram de perto.",
                    "Essa cena fala conosco. É possível honrar Cristo em público e esquecê-lo no cotidiano. É possível cantar sobre sua presença e, ao voltar para casa, retomar uma vida onde Ele não participa das decisões, das conversas, dos afetos e das prioridades.",
                ],
            ),
            (
                "Betânia como lugar de acolhimento",
                [
                    "Betânia não tinha o brilho de Jerusalém, mas tinha espaço para Jesus. Ali havia amizade, mesa, escuta e intimidade. Talvez a vida cristã amadureça justamente quando deixamos de oferecer apenas ramos e começamos a oferecer casa.",
                    "A fé que sustenta não é feita apenas de momentos fortes. Ela se revela na rotina: no modo como tratamos as pessoas, no que fazemos quando ninguém vê, no que permitimos ocupar nosso coração quando o barulho diminui.",
                    "Ser Betânia é transformar a vida comum em lugar de permanência para Cristo. É abrir a agenda, a casa, os pensamentos e as escolhas para que Ele não seja apenas visitado em ocasiões especiais, mas reconhecido como Senhor de tudo.",
                ],
            ),
            (
                "Uma pergunta para a alma",
                [
                    "Depois da festa, Jesus permanece conosco? Essa pergunta não vem para nos esmagar, mas para nos chamar de volta ao essencial. Cristo não busca somente aclamação; Ele deseja comunhão.",
                    "Talvez hoje seja um bom dia para trocar a pressa por presença. Para fazer uma oração simples. Para entregar a Ele aquilo que ficou fechado. Para dizer, com sinceridade: Senhor, não quero apenas celebrar o teu nome; quero que habites em mim.",
                ],
            ),
        ],
    },
    {
        "title": "Feitos para brilhar pela Palavra da Vida",
        "slug": "feitos-para-brilhar-pela-palavra-da-vida",
        "category": "Estudo Bíblico",
        "date": "2026-05-10",
        "author": "Pastor Antonio Lemos Filho",
        "image": "feitos-para-brilhar.png",
        "alt": "Bíblia aberta sobre mesa sob céu estrelado antes do amanhecer",
        "excerpt": "Uma meditação em Filipenses 2 sobre uma fé que abandona a murmuração e se apega à Palavra da Vida.",
        "quote": "Façam tudo sem murmurações nem discussões... apegando-se firmemente à palavra da vida. Filipenses 2:14-16",
        "sections": [
            (
                "Uma luz no meio da geração",
                [
                    "Paulo escreve aos filipenses com uma imagem forte: os filhos de Deus brilham como estrelas no mundo. Não é um brilho de vaidade, nem de aparência religiosa. É o testemunho silencioso e firme de uma vida atravessada pela Palavra.",
                    "Esse brilho aparece em coisas muito práticas. Paulo fala sobre murmurações e discussões. Ele sabe que a fé não se manifesta apenas em grandes declarações, mas também no tom da nossa fala, na forma como reagimos às frustrações e no modo como lidamos com pessoas difíceis.",
                    "A murmuração parece pequena, mas corrói a confiança. Quando o coração se acostuma a reclamar, ele passa a interpretar a vida pela falta, não pela fidelidade de Deus. Aos poucos, a alma deixa de descansar e começa a resistir.",
                ],
            ),
            (
                "A Palavra que sustenta",
                [
                    "Paulo não chama a igreja para um moralismo frio. Ele aponta para uma vida sustentada por Deus. Antes de falar do comportamento visível, ele lembra que Deus opera em nós tanto o querer quanto o realizar.",
                    "Por isso, brilhar não é fingir força. É permanecer ligado à fonte. É apegar-se à Palavra da Vida quando a mente se dispersa, quando a emoção oscila e quando o caminho parece escuro.",
                    "A Palavra nos realinha. Ela confronta a queixa, cura a percepção, devolve esperança e nos ensina a enxergar Deus mesmo nos dias comuns. Quem se apega à Palavra não se torna insensível; torna-se enraizado.",
                ],
            ),
            (
                "Um convite à paz interior",
                [
                    "Talvez o primeiro sinal de luz não seja falar mais alto, mas murmurar menos. Talvez seja aprender a responder com mansidão, agradecer com honestidade e permanecer fiel mesmo sem aplauso.",
                    "A vida cristã brilha quando a alma deixa de ser governada pelo resmungo e passa a ser conduzida pela presença de Cristo. Não precisamos fabricar luz. Precisamos permanecer nEle. A luz que vem da Palavra encontra caminho em uma vida rendida.",
                ],
            ),
        ],
    },
    {
        "title": "O coração desordenado",
        "slug": "o-coracao-desordenado",
        "category": "Formação Interior",
        "date": "2026-05-10",
        "author": "Pastor Antonio Lemos Filho",
        "image": "coracao-desordenado.png",
        "alt": "Mesa de estudo com Bíblia aberta, papéis e vaso de barro rachado derramando água",
        "excerpt": "Uma reflexão sobre guardar o coração, ordenar os afetos e permitir que Deus cure a vida por dentro.",
        "quote": "Sobre tudo o que se deve guardar, guarda o coração, porque dele procedem as fontes da vida. Provérbios 4:23",
        "sections": [
            (
                "A vida começa por dentro",
                [
                    "A Bíblia trata o coração como o centro da pessoa. Não apenas o lugar das emoções, mas também dos desejos, pensamentos, decisões e prioridades. O coração é o lugar onde a vida ganha direção.",
                    "Jesus disse que onde está o nosso tesouro, ali estará também o nosso coração. Isso significa que aquilo que consideramos precioso começa a governar nossa atenção, nosso tempo e nossas escolhas.",
                    "Quando o coração se desordena, a vida externa começa a mostrar sinais. A agenda pesa, os relacionamentos se desgastam, a ansiedade ocupa espaço demais e o essencial vai sendo empurrado para longe.",
                ],
            ),
            (
                "Guardar não é esconder",
                [
                    "Provérbios nos chama a guardar o coração. Guardar não significa fechar-se para a vida, endurecer os afetos ou fugir das pessoas. Significa vigiar com sabedoria aquilo que entra, permanece e governa o interior.",
                    "Um coração sem cuidado se torna vulnerável a falsos tesouros. Ele pode se apegar ao controle, à aprovação, à comparação, à pressa ou à dor. Aos poucos, essas coisas deixam de ser apenas experiências e passam a ocupar o lugar de direção.",
                    "Deus não deseja apenas organizar nossa rotina; Ele deseja curar nossa fonte. Quando a fonte é tratada, o fluxo muda. Quando o coração encontra seu lugar diante de Deus, a vida começa a respirar de outro modo.",
                ],
            ),
            (
                "Voltar ao centro",
                [
                    "A pergunta decisiva talvez seja: o que tem ocupado o centro do meu coração? Nem sempre a resposta vem rápido, mas ela costuma aparecer nos medos que nos dominam, nas buscas que nos consomem e nas perdas que parecem nos definir.",
                    "Cristo nos chama a uma ordem mais profunda. Não a ordem rígida de quem controla tudo, mas a paz de quem volta ao centro correto. Um coração entregue a Deus não deixa de sentir, mas aprende a não ser governado por tudo o que sente.",
                    "Guardar o coração é voltar, todos os dias, à presença daquele que conhece nossas fontes. É permitir que Deus reorganize o amor, purifique os desejos e devolva inteireza à alma.",
                ],
            ),
        ],
    },
]


STATIC_PAGES = {
    "sobre": {
        "title": "Sobre | Verbo Vivo",
        "description": "Conheça o propósito editorial do Verbo Vivo, um blog de reflexões cristãs para fortalecer a fé na vida cotidiana.",
        "heading": "Sobre o Verbo Vivo",
        "eyebrow": "Nossa casa",
        "body": [
            ("Uma palavra para a caminhada", [
                "O Verbo Vivo nasceu como um espaço de reflexão cristã para pessoas que buscam alento espiritual, clareza bíblica e uma fé que alcance a vida comum.",
                "Aqui, os textos procuram unir profundidade e simplicidade. A intenção não é produzir debates frios, mas oferecer leituras que ajudem o coração a voltar para Deus com sinceridade.",
            ]),
            ("Nossa linha editorial", [
                "Publicamos reflexões, estudos bíblicos e textos devocionais com linguagem acolhedora, responsabilidade espiritual e respeito à fé cristã.",
                "Cada publicação é preparada para preservar a centralidade de Cristo, a reverência às Escrituras e a atenção ao leitor que chega procurando consolo, direção ou fortalecimento.",
            ]),
            ("Compromisso", [
                "O Verbo Vivo não substitui acompanhamento pastoral, aconselhamento profissional ou cuidado médico quando eles forem necessários. Nosso papel é oferecer conteúdo reflexivo e edificante.",
            ]),
            ("Sobre o Autor das reflexões", [
                "As reflexões publicadas neste espaço são de autoria do Pastor Antonio Lemos Filho.",
                "Em breve, esta página receberá uma apresentação mais completa sobre sua trajetória, chamado, ministério e contribuição para a edificação da fé cristã.",
            ]),
        ],
    },
    "faq": {
        "title": "FAQ | Verbo Vivo",
        "description": "Perguntas frequentes sobre o Verbo Vivo, seus textos, uso de conteúdo e política editorial.",
        "heading": "Perguntas frequentes",
        "eyebrow": "FAQ",
        "body": [
            ("O que é o Verbo Vivo?", [
                "É um blog cristão dedicado a reflexões bíblicas, textos devocionais e estudos escritos em linguagem acessível para fortalecer a fé no cotidiano.",
            ]),
            ("Os textos substituem aconselhamento pastoral?", [
                "Não. Os textos têm finalidade reflexiva e espiritual. Em situações de sofrimento intenso, conflitos graves, saúde mental ou decisões delicadas, procure também apoio pastoral, familiar e profissional adequado.",
            ]),
            ("Posso compartilhar os artigos?", [
                "Sim. Você pode compartilhar os links dos artigos, preservando o nome do Verbo Vivo e sem alterar o conteúdo original.",
            ]),
            ("Posso copiar textos do blog em outro site?", [
                "Para republicação integral, adaptação ou uso comercial, entre em contato previamente com o responsável pelo blog. Citações breves com referência e link para a página original são bem-vindas.",
            ]),
            ("O blog coleta dados pessoais?", [
                "No modelo atual, o blog é essencialmente informativo. Não há cadastro de usuários nem formulário ativo. Dados técnicos de acesso podem ser tratados por serviços de hospedagem e infraestrutura, conforme explicado na Política de Privacidade.",
            ]),
        ],
    },
    "politica-de-privacidade": {
        "title": "Política de Privacidade | Verbo Vivo",
        "description": "Política de Privacidade do Verbo Vivo, com informações sobre dados pessoais, cookies e direitos do titular conforme a LGPD.",
        "heading": "Política de Privacidade",
        "eyebrow": "Privacidade",
        "body": [
            ("1. Sobre esta política", [
                "Esta Política de Privacidade explica, de forma clara, como o Verbo Vivo trata informações relacionadas aos visitantes do site, em conformidade com a Lei Geral de Proteção de Dados Pessoais, Lei nº 13.709/2018, conhecida como LGPD.",
                "O Verbo Vivo é um blog de conteúdo cristão. No momento, não possui cadastro de usuários, área de login, comentários públicos ou formulário de contato ativo.",
            ]),
            ("2. Quais dados podem ser tratados", [
                "Podem ser tratados dados técnicos gerados durante a navegação, como endereço IP, tipo de navegador, dispositivo, páginas acessadas, data e horário de acesso e informações semelhantes necessárias para funcionamento, segurança e melhoria do site.",
                "Caso futuramente sejam adicionados formulários, newsletter, comentários, analytics ou publicidade, esta política deverá ser atualizada para explicar quais dados serão coletados, para quais finalidades e com quais bases legais.",
            ]),
            ("3. Finalidades do tratamento", [
                "Os dados técnicos podem ser utilizados para disponibilizar o site, manter a segurança da infraestrutura, identificar falhas, prevenir abuso, medir desempenho e compreender de forma geral como o conteúdo é acessado.",
                "Não vendemos dados pessoais e não usamos, no modelo atual, cadastro próprio para criar perfis individuais de leitores.",
            ]),
            ("4. Cookies e tecnologias semelhantes", [
                "O site pode utilizar cookies estritamente necessários ao funcionamento da hospedagem e de recursos técnicos. Caso sejam ativados cookies de analytics, publicidade ou personalização, o visitante deverá receber informações adequadas e, quando exigido, opção de consentimento.",
                "Você pode gerenciar cookies diretamente nas configurações do seu navegador. A desativação de alguns cookies pode afetar o funcionamento de partes do site.",
            ]),
            ("5. Compartilhamento", [
                "Dados técnicos podem ser processados por provedores de infraestrutura, hospedagem e segurança necessários para manter o site disponível, como a plataforma de hospedagem utilizada.",
                "Também poderemos compartilhar informações quando houver obrigação legal, ordem de autoridade competente ou necessidade de proteger direitos e segurança do site e de terceiros.",
            ]),
            ("6. Segurança e retenção", [
                "Adotamos medidas razoáveis para proteger as informações tratadas no contexto do site. Ainda assim, nenhum ambiente digital é absolutamente imune a riscos.",
                "Dados técnicos são mantidos pelo tempo necessário às finalidades descritas nesta política ou conforme prazos aplicáveis pelos serviços de infraestrutura utilizados.",
            ]),
            ("7. Direitos do titular", [
                "Nos termos da LGPD, o titular pode solicitar confirmação de tratamento, acesso, correção, anonimização, bloqueio, eliminação, portabilidade quando aplicável, informação sobre compartilhamento e revisão de decisões automatizadas quando existirem.",
                "Como o site não possui cadastro ativo, algumas solicitações poderão depender da identificação mínima necessária para localizar eventual dado relacionado ao pedido.",
            ]),
            ("8. Contato", [
                "Para exercer direitos de titular ou tratar de privacidade, utilize o canal de contato que vier a ser indicado oficialmente no site. Até que uma página de contato seja publicada, solicitações podem ser feitas pelos canais públicos associados ao projeto.",
            ]),
            ("9. Atualizações", [
                "Esta política poderá ser atualizada para refletir mudanças no site, em seus serviços ou na legislação aplicável. A data da versão deve ser revisada sempre que houver alteração relevante.",
                "Última atualização: 12 de maio de 2026.",
            ]),
        ],
    },
}

CONTACT_EMAILS = [
    {
        "email": "contato@verbovivo.blog",
        "label": "Contato geral",
        "description": "Canal público para mensagens, sugestões, testemunhos, pedidos de correção e assuntos gerais sobre o Verbo Vivo.",
    },
]


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def content_sections(sections: list[tuple[str, list[str]]]) -> str:
    chunks: list[str] = []
    for heading, paragraphs in sections:
        chunks.append(f"<h2>{esc(heading)}</h2>")
        chunks.extend(f"<p>{esc(paragraph)}</p>" for paragraph in paragraphs)
    return "\n".join(chunks)


def page_shell(title: str, description: str, body: str, canonical: str, image: str | None = None, prefix: str = "") -> str:
    og_image = f"{DOMAIN}/images/articles/{image}" if image else f"{DOMAIN}/images/articles/depois-da-festa.png"
    return f"""<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{esc(title)}</title>
    <meta name="description" content="{esc(description)}" />
    <link rel="canonical" href="{canonical}" />
    <meta property="og:type" content="website" />
    <meta property="og:title" content="{esc(title)}" />
    <meta property="og:description" content="{esc(description)}" />
    <meta property="og:image" content="{og_image}" />
    <meta property="og:url" content="{canonical}" />
    <meta name="twitter:card" content="summary_large_image" />
    <link rel="alternate" type="application/rss+xml" title="Verbo Vivo" href="{prefix}feed.xml" />
    <link rel="stylesheet" href="{prefix}styles.css" />
  </head>
  <body>
    <header class="site-header">
      <a class="brand" href="{prefix}index.html">
        <span class="brand-mark">VV</span>
        <span>
          <strong>Verbo Vivo</strong>
          <small>verbovivo.blog</small>
        </span>
      </a>
      <nav aria-label="Navegação principal">
        <a href="{prefix}index.html#artigos">Artigos</a>
        <a href="{prefix}sobre.html">Sobre</a>
        <a href="{prefix}contato.html">Contato</a>
        <a href="{prefix}faq.html">FAQ</a>
        <a href="{prefix}politica-de-privacidade.html">Privacidade</a>
      </nav>
    </header>
    {body}
    <footer class="site-footer">
      <p><strong>Verbo Vivo</strong> publica reflexões cristãs para fortalecer a fé na vida cotidiana.</p>
      <div>
        <a href="{prefix}sobre.html">Sobre</a>
        <a href="{prefix}contato.html">Contato</a>
        <a href="{prefix}faq.html">FAQ</a>
        <a href="{prefix}politica-de-privacidade.html">Privacidade</a>
        <a href="{prefix}feed.xml">RSS</a>
      </div>
    </footer>
  </body>
</html>
"""


def article_card(article: dict, featured: bool = False, prefix: str = "") -> str:
    cls = "featured" if featured else "article-card"
    return f"""
      <article class="{cls}">
        <a href="{prefix}artigos/{article['slug']}.html">
          <img src="{prefix}images/articles/{article['image']}" alt="{esc(article['alt'])}" />
        </a>
        <div class="article-body">
          <p class="category">{esc(article['category'])}</p>
          <h3><a href="{prefix}artigos/{article['slug']}.html">{esc(article['title'])}</a></h3>
          <p>{esc(article['excerpt'])}</p>
        </div>
      </article>
"""


def build_index(articles: list[dict]) -> None:
    featured = articles[0]
    cards = "\n".join(article_card(article) for article in articles)
    body = f"""
    <main>
      <section class="hero">
        <div class="hero-copy">
          <p class="eyebrow">Palavra, fé e vida cristã</p>
          <h1>Reflexões cristãs para aquietar a alma e fortalecer a caminhada.</h1>
          <p>
            O Verbo Vivo reúne textos de fé, consolo e formação interior para quem
            procura uma leitura bíblica sensível, profunda e próxima da vida real.
          </p>
        </div>
        {article_card(featured, featured=True)}
      </section>

      <section class="section-intro" id="artigos">
        <p class="eyebrow">Reflexões recentes</p>
        <h2>Textos para ler com calma, oração e coração aberto</h2>
      </section>

      <section class="article-grid" aria-label="Lista de artigos">
        {cards}
      </section>

      <section class="editorial" id="editorial">
        <div>
          <p class="eyebrow">Linha editorial</p>
          <h2>Conteúdo cristão com reverência bíblica, clareza e cuidado com o leitor.</h2>
        </div>
        <div class="principles">
          <p>Textos preparados para edificação espiritual, consolo e reflexão.</p>
          <p>Linguagem acessível, sem abrir mão de profundidade bíblica.</p>
          <p>Compromisso com respeito, responsabilidade e centralidade em Cristo.</p>
        </div>
      </section>

      <section class="about" id="sobre">
        <p class="eyebrow">Sobre o projeto</p>
        <h2>Uma casa digital para Palavra, fé e vida cristã.</h2>
        <p>
          O Verbo Vivo existe para oferecer leituras que ajudem a alma a respirar,
          reencontrar esperança e caminhar com Deus nos dias simples e nos dias difíceis.
        </p>
      </section>
    </main>
"""
    output = page_shell(
        "Verbo Vivo | Reflexões cristãs",
        "Reflexões cristãs, estudos bíblicos e textos de alento espiritual para fortalecer a fé na vida cotidiana.",
        body,
        f"{DOMAIN}/",
    )
    (SITE / "index.html").write_text(output, encoding="utf-8")


def build_article(article: dict) -> None:
    body_html = content_sections(article["sections"])
    body = f"""
    <main>
      <article class="article-page">
        <header class="article-hero">
          <div>
            <p class="category">{esc(article['category'])}</p>
            <h1>{esc(article['title'])}</h1>
            <p class="article-excerpt">{esc(article['excerpt'])}</p>
            <p class="article-meta">Por {esc(article['author'])} · {article['date']}</p>
          </div>
          <img src="../images/articles/{article['image']}" alt="{esc(article['alt'])}" />
        </header>
        <div class="article-content">
          <blockquote>{esc(article['quote'])}</blockquote>
          {body_html}
        </div>
      </article>
    </main>
"""
    output = page_shell(
        f"{article['title']} | Verbo Vivo",
        article["excerpt"],
        body,
        f"{DOMAIN}/artigos/{article['slug']}.html",
        article["image"],
        "../",
    )
    (ARTICLE_DIR / f"{article['slug']}.html").write_text(output, encoding="utf-8")


def build_static_page(slug: str, page: dict) -> None:
    body_html = content_sections(page["body"])
    body = f"""
    <main>
      <article class="article-page static-page">
        <header class="plain-hero">
          <p class="eyebrow">{esc(page['eyebrow'])}</p>
          <h1>{esc(page['heading'])}</h1>
          <p class="article-excerpt">{esc(page['description'])}</p>
        </header>
        <div class="article-content">
          {body_html}
        </div>
      </article>
    </main>
"""
    output = page_shell(page["title"], page["description"], body, f"{DOMAIN}/{slug}.html")
    (SITE / f"{slug}.html").write_text(output, encoding="utf-8")


def build_contact_page() -> None:
    cards = "\n".join(
        f"""
          <article class="contact-card">
            <p class="category">{esc(item['label'])}</p>
            <h2><a href="mailto:{esc(item['email'])}">{esc(item['email'])}</a></h2>
            <p>{esc(item['description'])}</p>
          </article>
"""
        for item in CONTACT_EMAILS
    )
    body = f"""
    <main>
      <section class="plain-hero contact-hero">
        <p class="eyebrow">Contato</p>
        <h1>Fale com o Verbo Vivo</h1>
        <p class="article-excerpt">
          Use este canal para falar conosco, enviar sugestões, pedir correções
          ou tratar de assuntos relacionados ao Verbo Vivo.
        </p>
      </section>

      <section class="contact-grid" aria-label="Canais de e-mail">
        {cards}
      </section>

      <section class="contact-form-section">
        <div>
          <p class="eyebrow">Formulário</p>
          <h2>Envie uma mensagem</h2>
          <p>
            Este formulário abre seu aplicativo de e-mail com os campos preenchidos.
            Revise a mensagem antes de enviar.
          </p>
        </div>
        <form class="contact-form" action="mailto:contato@verbovivo.blog" method="post" enctype="text/plain">
          <label>
            Nome
            <input name="Nome" type="text" autocomplete="name" required />
          </label>
          <label>
            E-mail
            <input name="Email" type="email" autocomplete="email" required />
          </label>
          <label>
            Assunto
            <input name="Assunto" type="text" required />
          </label>
          <label>
            Tipo de mensagem
            <select name="Tipo">
              <option>Contato geral</option>
              <option>Envio de artigo</option>
              <option>Pedido de correção</option>
              <option>Assunto administrativo</option>
            </select>
          </label>
          <label class="full">
            Mensagem
            <textarea name="Mensagem" rows="7" required></textarea>
          </label>
          <button type="submit">Enviar por e-mail</button>
        </form>
      </section>
    </main>
"""
    output = page_shell(
        "Contato | Verbo Vivo",
        "Entre em contato com o Verbo Vivo ou envie artigos e reflexões para preparação editorial.",
        body,
        f"{DOMAIN}/contato.html",
    )
    (SITE / "contato.html").write_text(output, encoding="utf-8")


def build_css() -> None:
    css = """
:root {
  --ink: #17201b;
  --muted: #59645c;
  --paper: #fbfaf6;
  --cream: #efe6d4;
  --line: #d8d0bf;
  --sage: #4f7059;
  --gold: #a9792e;
  --white: #fffdf8;
  --shadow: 0 18px 50px rgba(23, 32, 27, 0.09);
}

* {
  box-sizing: border-box;
}

html {
  background: var(--paper);
  color: var(--ink);
  font-family: Arial, Helvetica, sans-serif;
  scroll-behavior: smooth;
}

body {
  margin: 0;
}

a {
  color: inherit;
  text-decoration: none;
}

img {
  display: block;
  max-width: 100%;
}

.site-header {
  align-items: center;
  background: rgba(251, 250, 246, 0.94);
  border-bottom: 1px solid var(--line);
  display: flex;
  gap: 24px;
  justify-content: space-between;
  padding: 18px clamp(18px, 4vw, 64px);
  position: sticky;
  top: 0;
  z-index: 5;
}

.brand {
  align-items: center;
  display: inline-flex;
  gap: 12px;
}

.brand-mark {
  align-items: center;
  background: var(--ink);
  border-radius: 50%;
  color: var(--paper);
  display: inline-flex;
  font-weight: 700;
  height: 42px;
  justify-content: center;
  width: 42px;
}

.brand strong,
.brand small {
  display: block;
}

.brand strong {
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.15rem;
}

.brand small {
  color: var(--muted);
  font-size: 0.78rem;
}

nav {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
}

nav a {
  color: var(--muted);
  font-size: 0.92rem;
  font-weight: 700;
}

main {
  overflow: hidden;
}

.hero {
  display: grid;
  gap: clamp(24px, 4vw, 48px);
  grid-template-columns: minmax(0, 0.9fr) minmax(320px, 1.1fr);
  padding: clamp(36px, 7vw, 88px) clamp(18px, 4vw, 64px) clamp(30px, 6vw, 72px);
}

.hero-copy {
  align-self: center;
  max-width: 650px;
}

.eyebrow,
.category {
  color: var(--sage);
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  margin: 0 0 12px;
  text-transform: uppercase;
}

h1,
h2,
h3 {
  font-family: Georgia, "Times New Roman", serif;
  letter-spacing: 0;
  margin: 0;
}

.hero h1 {
  font-size: clamp(2.25rem, 5vw, 5rem);
  line-height: 0.96;
  max-width: 820px;
}

.hero-copy p:last-child,
.about p,
.article-excerpt {
  color: var(--muted);
  font-size: 1.08rem;
  line-height: 1.7;
  max-width: 680px;
}

.featured,
.article-card {
  background: var(--white);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
}

.featured img,
.article-card img {
  aspect-ratio: 16 / 10;
  object-fit: cover;
  width: 100%;
}

.article-body {
  padding: clamp(18px, 3vw, 30px);
}

.article-body h3 {
  font-size: clamp(1.35rem, 2.2vw, 2rem);
  line-height: 1.08;
}

.article-body p:last-child {
  color: var(--muted);
  line-height: 1.6;
}

.section-intro,
.about {
  padding: 0 clamp(18px, 4vw, 64px);
}

.section-intro h2,
.about h2,
.editorial h2 {
  font-size: clamp(1.8rem, 3vw, 3.4rem);
  line-height: 1.02;
  max-width: 900px;
}

.article-grid {
  display: grid;
  gap: 22px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  padding: 28px clamp(18px, 4vw, 64px) clamp(40px, 6vw, 84px);
}

.editorial {
  background: var(--cream);
  border-block: 1px solid var(--line);
  display: grid;
  gap: 28px;
  grid-template-columns: 1fr 1fr;
  padding: clamp(36px, 6vw, 70px) clamp(18px, 4vw, 64px);
}

.principles {
  display: grid;
  gap: 14px;
}

.principles p {
  background: rgba(255, 253, 248, 0.58);
  border-left: 4px solid var(--gold);
  color: var(--muted);
  line-height: 1.55;
  margin: 0;
  padding: 14px 16px;
}

.about {
  padding-bottom: clamp(48px, 7vw, 96px);
  padding-top: clamp(42px, 7vw, 90px);
}

.article-page {
  padding: clamp(28px, 5vw, 70px) clamp(18px, 4vw, 64px) clamp(48px, 7vw, 96px);
}

.article-hero {
  align-items: center;
  display: grid;
  gap: clamp(24px, 5vw, 58px);
  grid-template-columns: minmax(0, 0.9fr) minmax(320px, 1.1fr);
  margin-bottom: clamp(34px, 6vw, 76px);
}

.plain-hero {
  margin: 0 auto clamp(34px, 6vw, 76px);
  max-width: 900px;
}

.article-hero h1,
.plain-hero h1 {
  font-size: clamp(2.3rem, 5vw, 5.4rem);
  line-height: 0.95;
}

.article-meta {
  color: var(--gold);
  font-weight: 800;
  margin-top: 22px;
}

.article-hero img {
  aspect-ratio: 16 / 10;
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
  object-fit: cover;
  width: 100%;
}

.article-content {
  margin-inline: auto;
  max-width: 820px;
}

.article-content h2 {
  font-size: clamp(1.55rem, 2.4vw, 2.35rem);
  line-height: 1.12;
  margin: 2.2em 0 0.65em;
}

.article-content h2:first-child {
  margin-top: 0;
}

.article-content p,
.article-content blockquote {
  color: #2d3831;
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(1.06rem, 1.4vw, 1.2rem);
  line-height: 1.86;
  margin: 0 0 1.15em;
}

.article-content blockquote {
  border-left: 4px solid var(--gold);
  color: var(--muted);
  padding-left: 18px;
}

.static-page .article-content p {
  font-family: Arial, Helvetica, sans-serif;
  font-size: 1.03rem;
  line-height: 1.75;
}

.contact-hero {
  padding: clamp(34px, 6vw, 72px) clamp(18px, 4vw, 64px) 0;
}

.contact-grid {
  display: grid;
  gap: 18px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  padding: 30px clamp(18px, 4vw, 64px) clamp(34px, 5vw, 60px);
}

.contact-card {
  background: var(--white);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
  padding: 22px;
}

.contact-card h2 {
  font-size: clamp(1.1rem, 1.5vw, 1.45rem);
  line-height: 1.15;
  overflow-wrap: anywhere;
}

.contact-card p:last-child {
  color: var(--muted);
  line-height: 1.6;
}

.contact-form-section {
  background: var(--cream);
  border-block: 1px solid var(--line);
  display: grid;
  gap: 30px;
  grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.2fr);
  padding: clamp(34px, 6vw, 72px) clamp(18px, 4vw, 64px);
}

.contact-form-section h2 {
  font-size: clamp(1.8rem, 3vw, 3.4rem);
  line-height: 1.02;
}

.contact-form-section p {
  color: var(--muted);
  line-height: 1.7;
  max-width: 520px;
}

.contact-form {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.contact-form label {
  color: var(--ink);
  display: grid;
  font-size: 0.9rem;
  font-weight: 800;
  gap: 7px;
}

.contact-form .full {
  grid-column: 1 / -1;
}

.contact-form input,
.contact-form select,
.contact-form textarea {
  background: var(--white);
  border: 1px solid var(--line);
  color: var(--ink);
  font: inherit;
  padding: 12px 13px;
  width: 100%;
}

.contact-form textarea {
  resize: vertical;
}

.contact-form button {
  background: var(--sage);
  border: 0;
  color: var(--white);
  cursor: pointer;
  font-weight: 800;
  padding: 13px 18px;
  width: max-content;
}

.site-footer {
  align-items: center;
  border-top: 1px solid var(--line);
  color: var(--muted);
  display: flex;
  gap: 20px;
  justify-content: space-between;
  padding: 28px clamp(18px, 4vw, 64px);
}

.site-footer p {
  margin: 0;
}

.site-footer div {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
}

.site-footer a {
  color: var(--sage);
  font-weight: 800;
}

@media (max-width: 900px) {
  .hero,
  .article-hero,
  .editorial {
    grid-template-columns: 1fr;
  }

  .hero {
    padding-top: 34px;
  }

  .article-grid {
    grid-template-columns: 1fr;
  }

  .contact-grid,
  .contact-form-section {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 620px) {
  .site-header {
    gap: 12px;
    padding: 12px 16px 10px;
  }

  .site-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .brand-mark {
    height: 36px;
    width: 36px;
  }

  .brand strong {
    font-size: 1rem;
  }

  .brand small {
    font-size: 0.72rem;
  }

  nav {
    gap: 8px;
    margin-inline: -16px;
    overflow-x: auto;
    padding: 2px 16px 4px;
    width: calc(100% + 32px);
  }

  nav a {
    border: 1px solid var(--line);
    border-radius: 999px;
    flex: 0 0 auto;
    font-size: 0.78rem;
    padding: 7px 10px;
  }

  .hero {
    display: flex;
    flex-direction: column;
    gap: 22px;
    padding: 26px 16px 34px;
  }

  .hero-copy {
    display: contents;
  }

  .hero-copy .eyebrow {
    order: 1;
  }

  .hero h1 {
    font-size: clamp(2.05rem, 13vw, 3.15rem);
    line-height: 0.98;
    order: 2;
  }

  .hero-copy p:last-child {
    font-size: 1rem;
    line-height: 1.55;
    margin: 0;
    order: 4;
  }

  .hero .featured {
    box-shadow: 0 12px 28px rgba(23, 32, 27, 0.08);
    order: 3;
  }

  .featured img,
  .article-card img {
    aspect-ratio: 4 / 3;
  }

  .article-body {
    padding: 16px;
  }

  .article-body h3 {
    font-size: 1.28rem;
    line-height: 1.12;
  }

  .article-body p:last-child {
    font-size: 0.96rem;
    line-height: 1.5;
  }

  .section-intro,
  .about {
    padding-inline: 16px;
  }

  .section-intro h2,
  .about h2,
  .editorial h2 {
    font-size: 1.75rem;
    line-height: 1.08;
  }

  .article-grid {
    gap: 16px;
    padding: 20px 16px 42px;
  }

  .editorial {
    gap: 22px;
    padding: 34px 16px;
  }

  .principles p {
    padding: 12px 14px;
  }

  .about {
    padding-bottom: 52px;
    padding-top: 38px;
  }

  .site-footer {
    padding: 24px 16px;
  }

  .contact-hero {
    padding: 30px 16px 0;
  }

  .contact-grid,
  .contact-form-section {
    padding-left: 16px;
    padding-right: 16px;
  }

  .contact-form {
    grid-template-columns: 1fr;
  }

  .contact-form button {
    width: 100%;
  }
}

@media (max-width: 380px) {
  .hero h1 {
    font-size: 1.92rem;
  }

  .hero-copy p:last-child {
    font-size: 0.96rem;
  }
}
"""
    (SITE / "styles.css").write_text(css.strip() + "\n", encoding="utf-8")


def build_sitemap(articles: list[dict]) -> None:
    urls = [f"{DOMAIN}/"]
    urls.extend(f"{DOMAIN}/artigos/{article['slug']}.html" for article in articles)
    urls.append(f"{DOMAIN}/contato.html")
    urls.extend(f"{DOMAIN}/{slug}.html" for slug in STATIC_PAGES)
    body = "\n".join(f"  <url><loc>{url}</loc></url>" for url in urls)
    sitemap = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n'
    (SITE / "sitemap.xml").write_text(sitemap, encoding="utf-8")


def build_feed(articles: list[dict]) -> None:
    items = []
    for article in articles:
        url = f"{DOMAIN}/artigos/{article['slug']}.html"
        items.append(
            f"""
    <item>
      <title>{esc(article['title'])}</title>
      <link>{url}</link>
      <guid>{url}</guid>
      <description>{esc(article['excerpt'])}</description>
      <pubDate>{date.fromisoformat(article['date']).strftime('%a, %d %b %Y 00:00:00 +0000')}</pubDate>
    </item>"""
        )
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Verbo Vivo</title>
    <link>{DOMAIN}/</link>
    <description>Reflexões cristãs para fortalecer a fé e iluminar a caminhada.</description>
{''.join(items)}
  </channel>
</rss>
"""
    (SITE / "feed.xml").write_text(feed, encoding="utf-8")


def build_misc() -> None:
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n", encoding="utf-8")
    (SITE / ".htaccess").write_text(
        """Options -Indexes
DirectoryIndex index.html

RewriteEngine On

RewriteCond %{THE_REQUEST} /index\\.html [NC]
RewriteRule ^index\\.html$ / [R=301,L]

RewriteCond %{REQUEST_FILENAME} !-d
RewriteCond %{REQUEST_FILENAME}.html -f
RewriteRule ^(.+?)/?$ $1.html [L]
""",
        encoding="utf-8",
    )
    (SITE / "humans.txt").write_text("Verbo Vivo\nConteúdo cristão para reflexão, consolo e formação espiritual.\n", encoding="utf-8")


def main() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)
    ARTICLE_DIR.mkdir(parents=True)
    IMAGE_OUT.mkdir(parents=True)
    for image in IMAGE_IN.glob("*.png"):
        shutil.copy2(image, IMAGE_OUT / image.name)

    build_css()
    build_index(ARTICLES)
    for article in ARTICLES:
        build_article(article)
    for slug, page in STATIC_PAGES.items():
        build_static_page(slug, page)
    build_contact_page()
    build_sitemap(ARTICLES)
    build_feed(ARTICLES)
    build_misc()
    print(SITE.resolve())


if __name__ == "__main__":
    main()
