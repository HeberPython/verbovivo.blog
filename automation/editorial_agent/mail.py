from __future__ import annotations

import smtplib
from email.message import EmailMessage
from html import escape

from imap_tools import MailBox, AND

from .config import settings


def unread_messages():
    with MailBox(settings.imap_host, settings.imap_port).login(settings.imap_user, settings.imap_password) as mailbox:
        for message in mailbox.fetch(AND(seen=False), mark_seen=True):
            yield message


def unread_publish_messages():
    with MailBox(settings.publish_imap_host, settings.publish_imap_port).login(
        settings.publish_imap_user,
        settings.publish_imap_password,
    ) as mailbox:
        for message in mailbox.fetch(AND(seen=False), mark_seen=True):
            yield message


def send_review_email(to_email: str, draft_title: str, review_url: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = f"Artigo pronto para aprovação: {draft_title}"
    msg["From"] = settings.smtp_user
    msg["To"] = to_email
    msg.set_content(f"Artigo pronto para revisão: {review_url}")
    msg.add_alternative(
        f"""
        <p>O artigo <strong>{escape(draft_title)}</strong> está pronto para revisão.</p>
        <p>
          <a href="{review_url}" style="display:inline-block;padding:12px 18px;background:#4f7059;color:white;text-decoration:none;font-weight:bold;">Abrir aprovação</a>
        </p>
        <p>Na página de revisão você poderá aprovar ou corrigir e publicar.</p>
        """,
        subtype="html",
    )
    with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)
