from __future__ import annotations

import smtplib
from email.message import EmailMessage
from html import escape

from imap_tools import AND, MailBox

from .config import settings
from .models import ArticleDraft


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


def email_article_preview(draft: ArticleDraft, review_url: str) -> str:
    image_html = ""
    if draft.image_filename:
        image_url = f"https://verbovivo.blog/images/articles/{escape(draft.image_filename)}"
        image_html = (
            f'<img src="{image_url}" alt="{escape(draft.title)}" '
            'style="display:block;width:100%;max-width:720px;border:1px solid #d8d0bf;margin:18px 0;" />'
        )

    approve_url = f"{review_url}#aprovar"
    correct_url = f"{review_url}#corrigir"
    return f"""
    <div style="background:#fbfaf6;color:#17201b;font-family:Arial,Helvetica,sans-serif;padding:24px;">
      <div style="max-width:760px;margin:0 auto;background:#fffdf8;border:1px solid #d8d0bf;padding:24px;">
        <p style="color:#4f7059;font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;margin:0 0 10px;">Verbo Vivo</p>
        <h1 style="font-family:Georgia,'Times New Roman',serif;font-size:34px;line-height:1.05;margin:0 0 12px;">
          {escape(draft.title)}
        </h1>
        <p style="color:#59645c;font-size:16px;line-height:1.6;margin:0 0 14px;">{escape(draft.excerpt)}</p>
        <p style="color:#a9792e;font-weight:800;margin:0 0 18px;">Por {escape(draft.author)}</p>
        {image_html}
        <div style="font-family:Georgia,'Times New Roman',serif;color:#2d3831;font-size:17px;line-height:1.75;">
          {draft.body_html}
        </div>
        <div style="border-top:1px solid #d8d0bf;margin-top:26px;padding-top:20px;">
          <a href="{approve_url}" style="display:inline-block;background:#4f7059;color:#fffdf8;text-decoration:none;font-weight:800;padding:13px 18px;margin:0 10px 10px 0;">
            Aprovar e publicar
          </a>
          <a href="{correct_url}" style="display:inline-block;background:#a9792e;color:#fffdf8;text-decoration:none;font-weight:800;padding:13px 18px;margin:0 0 10px 0;">
            Corrigir antes de publicar
          </a>
          <p style="color:#59645c;font-size:13px;line-height:1.5;margin:12px 0 0;">
            Por seguranca, a publicacao e feita no site do Verbo Vivo apos o clique. Correcoes abrem a caixa de edicao no navegador.
          </p>
        </div>
      </div>
    </div>
    """


def send_review_email(to_email: str, draft: ArticleDraft, review_url: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = f"Artigo pronto para aprovação: {draft.title}"
    msg["From"] = settings.smtp_user
    msg["To"] = to_email
    msg.set_content(
        f"Artigo pronto para revisão: {draft.title}\n\n"
        f"Aprovar e publicar: {review_url}#aprovar\n"
        f"Corrigir antes de publicar: {review_url}#corrigir\n"
    )
    msg.add_alternative(email_article_preview(draft, review_url), subtype="html")
    with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)
