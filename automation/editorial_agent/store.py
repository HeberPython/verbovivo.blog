from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import ArticleDraft


ROOT = Path(__file__).resolve().parents[2]
DRAFT_DIR = ROOT / "_drafts"
DRAFT_DIR.mkdir(parents=True, exist_ok=True)


def save_draft(draft: ArticleDraft) -> None:
    path = DRAFT_DIR / f"{draft.id}.json"
    path.write_text(json.dumps(asdict(draft), ensure_ascii=False, indent=2), encoding="utf-8")


def load_draft(draft_id: str) -> ArticleDraft:
    path = DRAFT_DIR / f"{draft_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return ArticleDraft(**data)


def find_by_token(token: str) -> ArticleDraft | None:
    for path in DRAFT_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("token") == token:
            return ArticleDraft(**data)
    return None

