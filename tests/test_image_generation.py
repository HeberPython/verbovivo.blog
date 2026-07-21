import unittest
import urllib.error
from io import BytesIO

from automation.editorial_agent.ai import build_image_generation_prompt, first_gemini_image_base64, gemini_http_error_message
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


if __name__ == "__main__":
    unittest.main()
