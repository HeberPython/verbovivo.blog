import unittest
import urllib.error
from io import BytesIO

from automation.editorial_agent.ai import first_gemini_image_base64, gemini_http_error_message


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


if __name__ == "__main__":
    unittest.main()
