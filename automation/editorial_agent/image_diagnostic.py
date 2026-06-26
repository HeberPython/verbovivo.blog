from __future__ import annotations

from pathlib import Path

from PIL import Image

from .ai import generate_cover_image_with_gemini
from .models import ArticleDraft


def main() -> None:
    output_dir = Path("automation/_diagnostics/gemini-image")
    draft = ArticleDraft(
        id="gemini-diagnostic",
        token="diagnostic",
        sender="diagnostic@verbovivo.blog",
        source_subject="Diagnostico de imagem",
        source_text="",
        title="Esperanca que renasce",
        slug="gemini-diagnostic",
        excerpt="Diagnostico isolado do gerador de imagens.",
        category="Reflexao",
        author="Antonio Lemos",
        body_html="",
        image_prompt=(
            "Uma estrada de pedras atravessa um campo verde ao amanhecer, conduzindo a uma cruz de madeira "
            "discreta no alto de uma colina. Luz dourada natural rompe as nuvens, com vegetacao viva, "
            "cores realistas, detalhes nitidos e atmosfera cristã de esperança e renovacao."
        ),
        image_filename="gemini-diagnostic.png",
    )

    image_path = generate_cover_image_with_gemini(draft, output_dir)
    if image_path is None:
        raise SystemExit("Gemini nao gerou a imagem de diagnostico.")

    with Image.open(image_path) as image:
        image.verify()
    with Image.open(image_path) as image:
        width, height = image.size
        image_format = image.format or "desconhecido"

    if width < 768 or height < 512:
        raise SystemExit(f"Imagem gerada com resolucao insuficiente: {width}x{height}.")

    print(f"Gemini validado: imagem {image_format}, {width}x{height}.")


if __name__ == "__main__":
    main()
