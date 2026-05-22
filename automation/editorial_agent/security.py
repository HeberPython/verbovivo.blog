from __future__ import annotations

import hashlib
import json
import secrets
from pathlib import Path

from .config import settings
from .mail import send_authorization_request


PENDING_DIR = Path("automation/_sender_authorizations")
ALLOWLIST_PATH = Path("automation/_allowed_senders.json")


def normalize_email(email: str) -> str:
    return email.strip().lower()


def configured_allowed_senders() -> set[str]:
    raw = settings.allowed_senders.replace(";", ",").replace("\n", ",")
    items = {normalize_email(item) for item in raw.split(",") if item.strip()}
    if settings.approver_email:
        items.add(normalize_email(settings.approver_email))
    items.add("hebergravano@gmail.com")
    if ALLOWLIST_PATH.exists():
        try:
            stored = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
            if isinstance(stored, list):
                items.update(normalize_email(str(item)) for item in stored if str(item).strip())
        except json.JSONDecodeError:
            pass
    return items


def message_key(inbox: str, sender: str, subject: str, message_id: str = "") -> str:
    value = f"{normalize_email(inbox)}|{normalize_email(sender)}|{subject.strip()}|{message_id.strip()}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def is_sender_allowed(sender: str) -> bool:
    return normalize_email(sender) in configured_allowed_senders()


def request_authorization_if_needed(sender: str, subject: str, inbox: str, message_id: str = "") -> bool:
    if is_sender_allowed(sender):
        return True
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    key = message_key(inbox, sender, subject, message_id)
    for path in PENDING_DIR.glob("*.json"):
        try:
            pending = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if pending.get("message_key") == key:
            print(f"Authorization already pending for {sender}")
            return False
    token = secrets.token_urlsafe(24)
    payload = {
        "token": token,
        "message_key": key,
        "flow": inbox,
        "sender": normalize_email(sender),
        "subject": subject,
        "message_id": message_id,
    }
    (PENDING_DIR / f"{token}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    base_url = settings.approval_base_url.rstrip("/")
    temporary_url = f"{base_url}/autorizar-remetente.php?token={token}&mode=temporary"
    permanent_url = f"{base_url}/autorizar-remetente.php?token={token}&mode=permanent"
    send_authorization_request(settings.approver_email, sender, subject, inbox, temporary_url, permanent_url)
    print(f"Blocked unauthorized sender and requested approval: {sender}")
    return False

