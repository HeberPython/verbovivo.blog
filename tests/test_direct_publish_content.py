import unittest

from automation.editorial_agent.content import ready_article_from_email


MESSY_EMAIL = """
Autor: Antonio Lemos

**Tema:** Plenitude Recebida: Completos em Cristo, o Soberano de Todas as

Coisas

**Texto-Chave:** Colossenses 2:10

**Palavra-Chave Exegetica:** pepleromenoi (Participio Perfeito Passivo:

"fomos preenchidos e continuamos cheios").

**1. A Natureza da Plenitude Crista (Colossenses 2:9-

10)**

O fundamento da nossa espiritualidade nao repousa em uma busca mistica por

algo que nos falta, mas na apropriacao daquilo que ja nos foi concedido.

> "porque nele habita corporalmente toda a plenitude da divindade;"

**2. A Suficiencia de Cristo contra as Fontes Secundarias**

Cristo e a origem, o conteudo e a garantia absoluta de tudo o que a igreja

necessita. O crescimento do crente acontece dentro da realidade que ja lhe pertence.
"""


class DirectPublishFormattingTests(unittest.TestCase):
    def test_reflows_email_wrapping_and_removes_markdown_residue(self):
        html = ready_article_from_email(
            "Plenitude Recebida", MESSY_EMAIL, "autor@example.com"
        ).body_html

        self.assertNotIn("Tema:", html)
        self.assertNotIn("Autor:", html)
        self.assertNotIn("**", html)
        self.assertNotIn("<p>Coisas</p>", html)
        self.assertIn("<h2>1. A Natureza da Plenitude Crista", html)
        self.assertIn("Colossenses, capítulo 2, versículos 9 a 10", html)
        self.assertIn("<blockquote>", html)
        self.assertIn("busca mistica por algo que nos falta", html)

    def test_seo_description_uses_article_prose_not_editorial_fields(self):
        draft = ready_article_from_email(
            "Plenitude Recebida",
            MESSY_EMAIL,
            "autor@example.com",
            "plenitude-recebida.jpg",
        )

        self.assertNotIn("Tema", draft.seo_description)
        self.assertNotIn("Texto-Chave", draft.seo_description)
        self.assertTrue(draft.seo_description.startswith("O fundamento"))


if __name__ == "__main__":
    unittest.main()
