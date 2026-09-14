import unittest
import urllib.error
from io import BytesIO

from automation.editorial_agent.ai import IMAGE_ERA_GUARDRAILS, SYSTEM_PROMPT, build_image_generation_prompt, first_gemini_image_base64, gemini_http_error_message
from automation.editorial_agent.models import ArticleDraft


class GeminiImageResponseTests(unittest.TestCase):
    def test_extracts_inline_image_from_gemini_response(self):
        data = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "ignored"},
                            {
                                "inlineData": {
                                    "mimeType": "image/png",
                                    "data": "aW1hZ2U=",
                                }
                            },
                        ]
                    }
                }
            ]
        }

        self.assertEqual(first_gemini_image_base64(data), "aW1hZ2U=")

    def test_returns_empty_when_gemini_response_has_no_image(self):
        data = {"candidates": [{"content": {"parts": [{"text": "no image"}]}}]}

        self.assertEqual(first_gemini_image_base64(data), "")

    def test_extracts_safe_gemini_http_error_message(self):
        error = urllib.error.HTTPError(
            url="https://example.invalid",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=BytesIO(b'{"error":{"message":"Model not found"}}'),
        )

        self.assertEqual(gemini_http_error_message(error), "Model not found")

    def test_image_prompt_contains_article_specific_guardrails(self):
        draft = ArticleDraft(
            id="id",
            token="token",
            sender="autor@example.com",
            source_subject="A Coroa da Virtude",
            source_text="",
            title="A Coroa da Virtude: O Amor como Apice da Vida Crista",
            slug="a-coroa-da-virtude",
            excerpt="Pedro apresenta o amor como maturidade visivel da fe.",
            category="Reflexao",
            author="Autor",
            body_html="<p>A fe amadurece em dominio proprio, perseveranca, piedade, fraternidade e amor.</p>",
            image_prompt="Uma cena concreta sobre maturidade crista e amor pratico.",
            image_filename="image.png",
        )

        prompt = build_image_generation_prompt(draft)

        self.assertIn("CONTEXTO ESPECIFICO DO ARTIGO", prompt)
        self.assertIn("A Coroa da Virtude", prompt)
        self.assertIn("Proibido usar por padrao", prompt)
        self.assertIn("imediatamente distinguivel", prompt)
        self.assertIn("pessoa isolada orando em paisagem bonita", prompt)

    def test_era_rules_reach_scene_editor_and_image_generator(self):
        self.assertIn(IMAGE_ERA_GUARDRAILS, SYSTEM_PROMPT)
        self.assertNotIn("ressurreicao, use arquitetura antiga", SYSTEM_PROMPT)
        for scene in (
            "Familias com roupas atuais reunidas em uma igreja no bairro.",
            "Comunidade crista dos primeiros seculos reunida em uma casa antiga.",
        ):
            with self.subTest(scene=scene):
                draft = ArticleDraft(
                    id="era-test", token="test-only", sender="autor@example.com",
                    source_subject="Comunidade", source_text=scene, title="Comunidade",
                    slug="comunidade", excerpt=scene, category="Reflexao", author="Autor",
                    body_html=f"<p>{scene}</p>", image_prompt=scene, image_filename="test.png",
                )
                before = draft.__dict__.copy()
                prompt = build_image_generation_prompt(draft)
                self.assertIn(IMAGE_ERA_GUARDRAILS, prompt)
                self.assertIn(scene, prompt)
                self.assertIn("igreja contemporanea semelhante as de hoje", prompt)
                self.assertIn("mantenha a ambientacao historica", prompt)
                self.assertIn("Nao modernize essas cenas", prompt)
                self.assertIn("Preserve os simbolos centrais", prompt)
                self.assertEqual(before, draft.__dict__)


if __name__ == "__main__":
    unittest.main()
