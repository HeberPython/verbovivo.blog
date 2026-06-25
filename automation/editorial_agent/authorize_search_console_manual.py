from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from google_auth_oauthlib.flow import InstalledAppFlow

from .audience_report import oauth_paths


SCOPES = ["https://www.googleapis.com/auth/webmasters"]
HOST = "localhost"
PORT = 8766


class OAuthHandler(BaseHTTPRequestHandler):
    server: "OAuthServer"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        code = params.get("code", [""])[0]
        error = params.get("error", [""])[0]
        if error:
            self.server.error = error
            self._respond("Autorizacao cancelada ou recusada. Pode fechar esta aba.")
            return
        if not code:
            self._respond("Codigo OAuth ausente. Pode fechar esta aba.")
            return
        self.server.code = code
        self._respond("Autorizacao concluida. Pode fechar esta aba e voltar ao Codex.")

    def log_message(self, format: str, *args) -> None:
        return

    def _respond(self, message: str) -> None:
        body = f"<!doctype html><meta charset='utf-8'><title>Search Console</title><p>{message}</p>"
        payload = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class OAuthServer(HTTPServer):
    code: str | None = None
    error: str | None = None


def main() -> None:
    client, token = oauth_paths()
    if not client or not client.exists():
        raise SystemExit("OAuth pendente: configure GSC_OAUTH_CLIENT_SECRETS com o JSON do cliente OAuth.")

    redirect_uri = f"http://{HOST}:{PORT}/"
    flow = InstalledAppFlow.from_client_secrets_file(str(client), scopes=SCOPES, redirect_uri=redirect_uri)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    url_file = Path(token).with_name("search-console-oauth-url.txt")
    status_file = Path(token).with_name("search-console-oauth-status.txt")
    url_file.write_text(auth_url, encoding="utf-8")
    status_file.write_text("Aguardando autorizacao do Google.", encoding="utf-8")
    print(f"URL salva em {url_file}")
    print(auth_url, flush=True)

    server = OAuthServer((HOST, PORT), OAuthHandler)
    while not server.code and not server.error:
        server.handle_request()

    if server.error:
        status_file.write_text(f"Erro OAuth: {server.error}", encoding="utf-8")
        raise SystemExit(f"Erro OAuth: {server.error}")

    flow.fetch_token(code=server.code)
    credentials = flow.credentials
    token.parent.mkdir(parents=True, exist_ok=True)
    token.write_text(credentials.to_json(), encoding="utf-8")
    status_file.write_text(f"Token OAuth salvo em {token}", encoding="utf-8")
    print(f"Token OAuth salvo em {token}")


if __name__ == "__main__":
    main()
