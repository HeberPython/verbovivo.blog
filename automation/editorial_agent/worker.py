from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from .ai import generate_cover_image, refine_with_openai
from .config import settings
from .content import ready_article_from_email, slugify
from .mail import send_review_email, unread_messages, unread_publish_messages
from .publisher import publish_article, upload_review_draft
from .store import save_draft


def extract_message_text(message) -> str:
    if message.text:
        return message.text
    if message.html:
        return message.html
    parts = []
    for attachment in message.attachments:
        if attachment.filename.lower().endswith((".txt", ".md")):
            parts.append(attachment.payload.decode("utf-8", errors="replace"))
    return "\n\n".join(parts)


def standardize_article_image(payload: bytes, path: Path) -> bool:
    try:
        with Image.open(BytesIO(payload)) as source:
            image = ImageOps.exif_transpose(source)
            image = ImageOps.fit(image, (1600, 1000), method=Image.Resampling.LANCZOS)
            if image.mode in {"RGBA", "LA"}:
                background = Image.new("RGB", image.size, (251, 250, 246))
                background.paste(image, mask=image.getchannel("A"))
                image = background
            else:
                image = image.convert("RGB")
            image.save(path, format="JPEG", quality=88, optimize=True, progressive=True)
        return True
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        print(f"Ignored invalid image attachment for direct publish: {exc.__class__.__name__}")
        return False


def save_first_image_attachment(message, slug: str) -> tuple[str, str]:
    output_dir = Path("automation/_publish_images")
    output_dir.mkdir(parents=True, exist_ok=True)
    for attachment in message.attachments:
        name = attachment.filename.lower()
        if name.endswith((".png", ".jpg", ".jpeg", ".webp")):
            filename = f"{slug}.jpg"
            path = output_dir / filename
            if standardize_article_image(attachment.payload, path):
                return filename, str(path)
    return "", ""


def is_service_email(message) -> bool:
    return message.from_.endswith("@email.hostinger.com")


def poll_once() -> None:
    for message in unread_messages():
        if is_service_email(message):
            print(f"Ignored service email: {message.subject}")
            continue
        source_text = extract_message_text(message)
        if not source_text.strip():
            continue
        draft = refine_with_openai(source_text, message.subject or "Nova reflexão", message.from_)
        generate_cover_image(draft, Path("automation/_generated_images"))
        save_draft(draft)
        upload_review_draft(draft)
        recipient = settings.approver_email or message.from_
        review_url = f"{settings.approval_base_url}/revisao.php?token={draft.token}"
        send_review_email(recipient, draft, review_url)
        print(f"Draft created: {draft.id} -> {review_url}")


def publish_once() -> None:
    for message in unread_publish_messages():
        if is_service_email(message):
            print(f"Ignored service email: {message.subject}")
            continue
        source_text = extract_message_text(message)
        if not source_text.strip():
            continue
        slug = slugify(message.subject or "nova-reflexao")
        image_filename, image_path = save_first_image_attachment(message, slug)
        draft = ready_article_from_email(message.subject or "Nova reflexão", source_text, message.from_, image_filename, image_path)
        save_draft(draft)
        publish_article(draft)
        print(f"Published directly: {draft.slug}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["poll-once", "publish-once"])
    args = parser.parse_args()
    if args.command == "poll-once":
        poll_once()
    elif args.command == "publish-once":
        publish_once()


if __name__ == "__main__":
    main()
