import unittest

from automation.editorial_agent.ai import first_gemini_image_base64


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


if __name__ == "__main__":
    unittest.main()
