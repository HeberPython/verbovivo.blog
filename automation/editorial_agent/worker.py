from __future__ import annotations

import argparse
from pathlib import Path

from .ai import generate_cover_image, refine_with_openai
from .config import settings
from .content import ready_article_from_email, slugify
from .mail import send_review_email, unread_messages, unread_publish_messages
from .publisher import publish_article
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


def save_first_image_attachment(message, slug: str) -> tuple[str, str]:
    output_dir = Path("automation/_publish_images")
    output_dir.mkdir(parents=True, exist_ok=True)
    for attachment in message.attachments:
        name = attachment.filename.lower()
        if name.endswith((".png", ".jpg", ".jpeg", ".webp")):
            suffix = Path(name).suffix or ".png"
            filename = f"{slug}{suffix}"
            path = output_dir / filename
            path.write_bytes(attachment.payload)
            return filename, str(path)
    return "", ""


def poll_once() -> None:
    for message in unread_messages():
        source_text = extract_message_text(message)
        if not source_text.strip():
            continue
        draft = refine_with_openai(source_text, message.subject or "Nova reflexão", message.from_)
        generate_cover_image(draft, Path("automation/_generated_images"))
        save_draft(draft)
        recipient = settings.approver_email or message.from_
        review_url = f"{settings.approval_base_url}/review/{draft.token}"
        send_review_email(recipient, draft.title, review_url)
        print(f"Draft created: {draft.id} -> {review_url}")


def publish_once() -> None:
    for message in unread_publish_messages():
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
