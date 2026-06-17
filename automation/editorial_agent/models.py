from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ArticleDraft:
    id: str
    token: str
    sender: str
    source_subject: str
    source_text: str
    title: str
    slug: str
    excerpt: str
    category: str
    author: str
    body_html: str
    image_prompt: str
    image_filename: str
    author_socials: dict[str, str] = field(default_factory=dict)
    seo_title: str = ""
    seo_description: str = ""
    seo_keywords: str = ""
    local_image_path: str = ""
    status: str = "pending_review"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
