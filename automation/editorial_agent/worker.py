from __future__ import annotations

import argparse

from .config import settings
from pathlib import Path

from .ai import generate_cover_image, refine_with_openai
from .mail import send_review_email, unread_messages
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["poll-once"])
    args = parser.parse_args()
    if args.command == "poll-once":
        poll_once()


if __name__ == "__main__":
    main()
