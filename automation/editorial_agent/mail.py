from __future__ import annotations

import smtplib
import imaplib
import ssl
from email.message import EmailMessage
from html import escape

from imap_tools import AND, MailBox

from .config import settings
from .content import author_socials_html
from .models import ArticleDraft


IMAP_CLOSE_ERRORS = (imaplib.IMAP4.abort, ssl.SSLError, OSError)


def _fetch_unread(host: str, port: int, user: str, password: str, limit: int | None = None):
    mailbox = MailBox(host, port).login(user, password)
    try:
        # Fetch everything up front, then close IMAP before OpenAI/FTP work starts.
        # Hostinger can close long-lived idle IMAP sockets while articles/images are processed.
        return list(mailbox.fetch(AND(seen=False), limit=limit, mark_seen=False))
    finally:
        try:
            mailbox.logout()
        except IMAP_CLOSE_ERRORS as exc:
            print(f"Warning: IMAP logout ignored after fetch: {exc.__class__.__name__}")


def unread_messages(limit: int | None = None):
    return _fetch_unread(settings.imap_host, settings.imap_port, settings.imap_user, settings.imap_password, limit=limit)


def unread_publish_messages():
    return _fetch_unread(
        settings.publish_imap_host,
        settings.publish_imap_port,
        settings.publish_imap_user,
        settings.publish_imap_password,
    )


def recent_publish_messages(limit: int = 25):
    mailbox = MailBox(settings.publish_imap_host, settings.publish_imap_port).login(
        settings.publish_imap_user,
        settings.publish_imap_password,
    )
    try:
        # Recovery path: Hostinger/webmail can show a message as read even when
        # the site update failed. Looking at recent messages prevents silent loss.
        return list(mailbox.fetch(limit=limit, reverse=True, mark_seen=False, headers_only=True))
    finally:
        try:
            mailbox.logout()
        except IMAP_CLOSE_ERRORS as exc:
            print(f"Warning: IMAP logout ignored after recent fetch: {exc.__class__.__name__}")


def publish_message_by_uid(uid: str | int):
    mailbox = MailBox(settings.publish_imap_host, settings.publish_imap_port).login(
        settings.publish_imap_user,
        settings.publish_imap_password,
    )
    try:
        messages = list(mailbox.fetch(AND(uid=str(uid)), limit=1, mark_seen=False))
        return messages[0] if messages else None
    finally:
        try:
            mailbox.logout()
        except IMAP_CLOSE_ERRORS as exc:
            print(f"Warning: IMAP logout ignored after uid fetch: {exc.__class__.__name__}")


def mark_seen(inbox: str, uid: str | int) -> None:
    if inbox == "publicar@verbovivo.blog":
        host = settings.publish_imap_host
        port = settings.publish_imap_port
        user = settings.publish_imap_user
        password = settings.publish_imap_password
    else:
        host = settings.imap_host
        port = settings.imap_port
        user = settings.imap_user
        password = settings.imap_password
    imap = imaplib.IMAP4_SSL(host, port)
    try:
        imap.login(user, password)
        imap.select("INBOX")
        status, _ = imap.uid("STORE", str(uid), "+FLAGS", r"(\Seen)")
        if status != "OK":
            raise RuntimeError(f"Could not mark message {uid} as seen in {inbox}.")
    finally:
        try:
            imap.logout()
        except IMAP_CLOSE_ERRORS as exc:
            print(f"Warning: IMAP logout ignored after mark_seen: {exc.__class__.__name__}")


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
        <p style="color:#a9792e;font-weight:800;margin:0 0 8px;">Por {escape(draft.author)}</p>
        <div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;margin:0 0 18px;">{author_socials_html(draft.author_socials)}</div>
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


def send_authorization_request(to_email: str, sender: str, subject: str, inbox: str, temporary_url: str, permanent_url: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = f"Autorizar remetente no Verbo Vivo: {sender}"
    msg["From"] = settings.smtp_user
    msg["To"] = to_email
    msg.set_content(
        "Um remetente ainda nao aprovado tentou enviar conteudo para o Verbo Vivo.\n\n"
        f"Remetente: {sender}\n"
        f"Caixa: {inbox}\n"
        f"Assunto: {subject}\n\n"
        f"Autorizar somente esta mensagem: {temporary_url}\n"
        f"Autorizar remetente permanente: {permanent_url}\n"
    )
    msg.add_alternative(
        f"""
        <div style="font-family:Arial,Helvetica,sans-serif;background:#fbfaf6;color:#17201b;padding:24px;">
          <div style="max-width:680px;margin:0 auto;background:#fffdf8;border:1px solid #d8d0bf;padding:24px;">
            <p style="color:#4f7059;font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;">Verbo Vivo</p>
            <h1 style="font-family:Georgia,'Times New Roman',serif;">Autorizar novo remetente?</h1>
            <p><strong>Remetente:</strong> {escape(sender)}</p>
            <p><strong>Caixa:</strong> {escape(inbox)}</p>
            <p><strong>Assunto:</strong> {escape(subject)}</p>
            <p>O agente bloqueou este envio porque o remetente ainda nao esta na lista aprovada.</p>
            <p>
              <a href="{escape(temporary_url)}" style="display:inline-block;background:#a9792e;color:#fffdf8;text-decoration:none;font-weight:800;padding:13px 18px;margin:0 10px 10px 0;">Autorizar somente este artigo</a>
              <a href="{escape(permanent_url)}" style="display:inline-block;background:#4f7059;color:#fffdf8;text-decoration:none;font-weight:800;padding:13px 18px;">Autorizar remetente permanente</a>
            </p>
          </div>
        </div>
        """,
        subtype="html",
    )
    with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)
