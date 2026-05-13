from __future__ import annotations

from html import escape

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse

from .models import ArticleDraft
from .publisher import publish_article
from .store import find_by_token, save_draft


app = FastAPI(title="Verbo Vivo Editorial Agent")


def page(content: str) -> HTMLResponse:
    return HTMLResponse(
        f"""<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Revisão editorial | Verbo Vivo</title>
    <style>
      body {{ font-family: Arial, sans-serif; margin: 0; background: #fbfaf6; color: #17201b; }}
      main {{ max-width: 920px; margin: 0 auto; padding: 32px 18px 80px; }}
      textarea {{ width: 100%; min-height: 420px; padding: 14px; font: 16px/1.6 Georgia, serif; }}
      button, a.button {{ border: 0; display: inline-block; margin: 10px 8px 0 0; padding: 12px 18px; text-decoration: none; font-weight: 700; cursor: pointer; }}
      .approve {{ background: #4f7059; color: white; }}
      .correct {{ background: #a9792e; color: white; }}
      .preview {{ background: white; border: 1px solid #d8d0bf; padding: 20px; }}
    </style>
  </head>
  <body><main>{content}</main></body>
</html>"""
    )


@app.get("/review/{token}", response_class=HTMLResponse)
def review(token: str):
    draft = find_by_token(token)
    if not draft:
        raise HTTPException(status_code=404, detail="Rascunho não encontrado")
    return page(
        f"""
        <h1>{escape(draft.title)}</h1>
        <p><strong>Categoria:</strong> {escape(draft.category)}</p>
        <p><strong>Resumo:</strong> {escape(draft.excerpt)}</p>
        <div class="preview">{draft.body_html}</div>
        <form action="/approve/{token}" method="post">
          <button class="approve" type="submit">Aprovar e publicar</button>
        </form>
        <form action="/correct/{token}" method="post">
          <h2>Corrigir e publicar</h2>
          <label>Título<br><input name="title" value="{escape(draft.title)}" style="width:100%;padding:10px;"></label>
          <p><label>Artigo em HTML<br><textarea name="body_html">{escape(draft.body_html)}</textarea></label></p>
          <button class="correct" type="submit">Enviar correção e publicar</button>
        </form>
        """
    )


@app.post("/approve/{token}", response_class=HTMLResponse)
def approve(token: str):
    draft = find_by_token(token)
    if not draft:
        raise HTTPException(status_code=404, detail="Rascunho não encontrado")
    draft.status = "approved"
    save_draft(draft)
    publish_article(draft)
    return page("<h1>Publicado</h1><p>O artigo foi aprovado e publicado no site.</p>")


@app.post("/correct/{token}", response_class=HTMLResponse)
def correct(token: str, title: str = Form(...), body_html: str = Form(...)):
    draft = find_by_token(token)
    if not draft:
        raise HTTPException(status_code=404, detail="Rascunho não encontrado")
    updated = ArticleDraft(**{**draft.__dict__, "title": title, "body_html": body_html, "status": "corrected_approved"})
    save_draft(updated)
    publish_article(updated)
    return page("<h1>Correção publicada</h1><p>O artigo corrigido foi publicado no site.</p>")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8787)

