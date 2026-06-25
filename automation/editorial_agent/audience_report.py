from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from ftplib import FTP
from pathlib import Path

from .config import ROOT
from .config import settings


SITE = ROOT / "site"


def env(name: str) -> str:
    return os.getenv(name, "").strip()


def configured_sources() -> dict[str, bool]:
    gsc_credentials = credentials_path()
    _, gsc_token = oauth_paths()
    hostinger_logs = env("HOSTINGER_ACCESS_LOG_PATH")
    analytics_local = project_path_from_env("HOSTINGER_ANALYTICS_LOCAL_LOG")
    return {
        "Google Analytics 4": bool(env("GA4_MEASUREMENT_ID")),
        "Google Search Console API": bool(env("GSC_SITE_URL") and ((gsc_credentials and gsc_credentials.exists()) or gsc_token.exists())),
        "Hostinger access logs": bool((hostinger_logs and expand_log_paths(hostinger_logs)) or (analytics_local and analytics_local.exists())),
        "Google AdSense": bool(env("GOOGLE_ADSENSE_CLIENT")),
        "Telegram": bool((env("TELEGRAM_BOT_TOKEN") or env("TELEGRAM_TOKEN")) and env("TELEGRAM_CHAT_ID")) or bool(env("TELEGRAM_GH_REPO") and env("TELEGRAM_GH_WORKFLOW")),
    }


def credentials_path() -> Path | None:
    value = env("GOOGLE_APPLICATION_CREDENTIALS")
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def search_console_summary() -> tuple[list[str], str | None]:
    path = credentials_path()
    site_url = env("GSC_SITE_URL")
    if not site_url:
        return [], None
    try:
        from googleapiclient.discovery import build
        from google.oauth2 import service_account
    except ImportError as exc:
        return [], f"Bibliotecas Google ausentes: {exc.name}"

    credentials, oauth_error = oauth_credentials()
    auth_method = "OAuth"
    if not credentials:
        auth_method = "conta de servico"
        if not path:
            return [], oauth_error or "Search Console pendente: autorize OAuth ou configure GOOGLE_APPLICATION_CREDENTIALS."
        if not path.exists():
            return [], f"Credencial Search Console nao encontrada em {path}"
        credentials = service_account.Credentials.from_service_account_file(
            str(path),
            scopes=["https://www.googleapis.com/auth/webmasters"],
        )

    try:
        service = build("searchconsole", "v1", credentials=credentials, cache_discovery=False)
        end = datetime.now(timezone.utc).date() - timedelta(days=2)
        start = end - timedelta(days=27)
        body = {
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "dimensions": ["query"],
            "rowLimit": 10,
        }
        response = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
    except Exception as exc:  # Google errors include detailed API messages here.
        return [], f"Falha ao consultar Search Console para {site_url} usando {auth_method}: {exc}"

    rows = response.get("rows", [])
    if not rows:
        return [f"Search Console conectado por {auth_method} para {site_url}, mas sem consultas no periodo {start} a {end}."], None
    lines = [f"Autenticacao: {auth_method}", f"Periodo: {start} a {end}"]
    for row in rows:
        query = row.get("keys", [""])[0]
        clicks = row.get("clicks", 0)
        impressions = row.get("impressions", 0)
        ctr = row.get("ctr", 0) * 100
        position = row.get("position", 0)
        lines.append(f"- {query}: {clicks} cliques, {impressions} impressoes, CTR {ctr:.2f}%, posicao media {position:.1f}")
    return lines, None


def project_path_from_env(name: str) -> Path | None:
    value = env(name)
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def oauth_paths() -> tuple[Path | None, Path]:
    client = project_path_from_env("GSC_OAUTH_CLIENT_SECRETS")
    token = project_path_from_env("GSC_OAUTH_TOKEN") or (ROOT / "automation" / "_credentials" / "search-console-oauth-token.json")
    return client, token


def authorize_search_console() -> str:
    client, token = oauth_paths()
    if not client or not client.exists():
        return "OAuth pendente: configure GSC_OAUTH_CLIENT_SECRETS com o JSON do cliente OAuth."
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        return f"Biblioteca OAuth ausente: {exc.name}"
    flow = InstalledAppFlow.from_client_secrets_file(
        str(client),
        scopes=["https://www.googleapis.com/auth/webmasters"],
    )
    credentials = flow.run_local_server(port=0, open_browser=False)
    token.parent.mkdir(parents=True, exist_ok=True)
    token.write_text(credentials.to_json(), encoding="utf-8")
    return f"Token OAuth salvo em {token}"


def oauth_credentials():
    client, token = oauth_paths()
    if not client or not client.exists() or not token.exists():
        return None, None
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError as exc:
        return None, f"Bibliotecas OAuth ausentes: {exc.name}"
    credentials = Credentials.from_authorized_user_file(
        str(token),
        scopes=["https://www.googleapis.com/auth/webmasters"],
    )
    if credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
        except Exception as exc:
            return None, f"Token OAuth invalido ou expirado; execute --authorize-search-console novamente. Detalhe: {exc}"
        token.write_text(credentials.to_json(), encoding="utf-8")
    if not credentials.valid:
        return None, "Token OAuth invalido; execute --authorize-search-console novamente."
    return credentials, None


def missing_sources() -> list[tuple[str, str, str]]:
    sources = configured_sources()
    missing: list[tuple[str, str, str]] = []
    if not sources["Google Analytics 4"]:
        missing.append(("Google Analytics 4", "GA4_MEASUREMENT_ID", "visitas, tempo medio, engajamento, dispositivos, geolocalizacao e origem de trafego"))
    if not sources["Google Search Console API"]:
        missing.append(("Google Search Console API", "GOOGLE_APPLICATION_CREDENTIALS e GSC_SITE_URL", "consultas de busca, impressoes, cliques, CTR e posicao media"))
    if not sources["Hostinger access logs"]:
        missing.append(("Hostinger access logs", "HOSTINGER_ACCESS_LOG_PATH", "paginas acessadas, IP/origem tecnica, status HTTP, erros 404 e leitura independente de cookies"))
    if not sources["Google AdSense"]:
        missing.append(("Google AdSense", "GOOGLE_ADSENSE_CLIENT", "monetizacao editorial se anuncios forem ativados"))
    if not sources["Telegram"]:
        missing.append(("Telegram", "TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID", "envio automatico do resumo semanal"))
    return missing


def load_articles() -> list[dict]:
    articles: list[dict] = []
    for path in sorted((SITE / "artigos").glob("*.html")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        title_match = re.search(r"<title>(.*?)</title>", text, flags=re.I | re.S)
        articles.append({"slug": path.stem, "title": title_match.group(1).split("|")[0].strip() if title_match else path.stem})
    return articles


def expand_log_paths(path_value: str) -> list[Path]:
    candidates: list[Path] = []
    for part in [item.strip() for item in path_value.split(";") if item.strip()]:
        path = Path(part)
        if not path.is_absolute():
            path = ROOT / path
        if any(char in str(path) for char in ["*", "?"]):
            candidates.extend(sorted(path.parent.glob(path.name)))
        elif path.is_dir():
            candidates.extend(sorted(file for file in path.rglob("*") if file.is_file()))
        else:
            candidates.append(path)
    return [
        path
        for path in candidates
        if path.exists() and path.suffix.lower() in {".log", ".txt", ".gz", ".jsonl", ""}
    ]


def download_hostinger_analytics_log() -> tuple[Path | None, str | None]:
    remote = env("HOSTINGER_ANALYTICS_REMOTE_LOG")
    local_value = env("HOSTINGER_ANALYTICS_LOCAL_LOG")
    if not remote or not local_value:
        return None, None
    local = Path(local_value)
    if not local.is_absolute():
        local = ROOT / local
    local.parent.mkdir(parents=True, exist_ok=True)
    try:
        with FTP() as ftp:
            ftp.connect(settings.ftp_host, settings.ftp_port, timeout=30)
            ftp.login(settings.ftp_user, settings.ftp_password)
            ftp.set_pasv(True)
            ftp.cwd(settings.ftp_dir)
            with local.open("wb") as file:
                ftp.retrbinary(f"RETR {remote}", file.write)
        return local, None
    except Exception as exc:
        return None, f"Log proprio ainda indisponivel em {remote}: {exc}"


def read_log_lines(path: Path) -> list[str]:
    if path.suffix.lower() == ".gz":
        with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as file:
            return file.read().splitlines()
    return path.read_text(encoding="utf-8", errors="ignore").splitlines()


def parse_logs(path_value: str) -> Counter[str]:
    paths = expand_log_paths(path_value)
    page_counts: Counter[str] = Counter()
    pattern = re.compile(r'"(?:GET|POST|HEAD) ([^" ?]+)')
    for path in paths:
        for line in read_log_lines(path):
            match = pattern.search(line)
            if not match:
                continue
            page = match.group(1)
            if page.endswith((".css", ".js", ".png", ".jpg", ".jpeg", ".webp", ".ico", ".xml")):
                continue
            page_counts[page] += 1
    return page_counts


def parse_first_party_events(path: Path | None) -> dict:
    if not path or not path.exists():
        return {}
    events: list[dict] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            events.append(item)
    if not events:
        return {}

    pageviews = [event for event in events if event.get("event") == "pageview"]
    pages = Counter(str(event.get("path", "")) for event in pageviews if event.get("path"))
    referrers = Counter(referrer_host(str(event.get("referrer", ""))) for event in pageviews)
    referrers.pop("", None)
    languages = Counter(str(event.get("language", "")) for event in pageviews if event.get("language"))
    timezones = Counter(str(event.get("timezone", "")) for event in pageviews if event.get("timezone"))

    max_elapsed_by_page_id: dict[str, int] = {}
    for event in events:
        page_id = str(event.get("page_id", ""))
        if not page_id:
            continue
        elapsed = int(event.get("elapsed_seconds") or 0)
        max_elapsed_by_page_id[page_id] = max(max_elapsed_by_page_id.get(page_id, 0), elapsed)
    avg_elapsed = sum(max_elapsed_by_page_id.values()) / len(max_elapsed_by_page_id) if max_elapsed_by_page_id else 0

    return {
        "events": len(events),
        "pageviews": len(pageviews),
        "sessions": len({str(event.get("session_id", "")) for event in events if event.get("session_id")}),
        "pages": pages,
        "referrers": referrers,
        "languages": languages,
        "timezones": timezones,
        "avg_elapsed": avg_elapsed,
    }


def referrer_host(value: str) -> str:
    if not value:
        return "Direto/sem referencia"
    try:
        parsed = urllib.parse.urlparse(value)
        return parsed.netloc or "Direto/sem referencia"
    except Exception:
        return "Referencia invalida"


def bar(label: str, value: int, max_value: int) -> str:
    width = 24
    filled = int((value / max_value) * width) if max_value else 0
    return f"{label[:34]:34} | {'#' * filled}{'.' * (width - filled)} {value}"


def build_report() -> tuple[str, str]:
    generated_at = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %z")
    sources = configured_sources()
    articles = load_articles()
    log_path_value = env("HOSTINGER_ACCESS_LOG_PATH")
    analytics_log, analytics_download_error = download_hostinger_analytics_log()
    analytics_data = parse_first_party_events(analytics_log)
    log_files = expand_log_paths(log_path_value) if log_path_value else []
    page_counts = parse_logs(log_path_value) if log_files else Counter()
    gsc_lines, gsc_error = search_console_summary()

    lines = [
        "# Relatorio editorial Verbo Vivo",
        "",
        f"Gerado em: {generated_at}",
        "",
        "## Fontes configuradas",
    ]
    for source, ok in sources.items():
        lines.append(f"- {source}: {'OK' if ok else 'pendente'}")

    lines.extend(["", "## Inventario editorial local", f"- Artigos encontrados: {len(articles)}"])
    if articles:
        for item in articles[:10]:
            lines.append(f"- {item.get('title') or item.get('slug')}")

    if page_counts:
        lines.extend(["", "## Paginas mais acessadas pelos logs", ""])
        max_value = max(page_counts.values())
        for page, count in page_counts.most_common(10):
            lines.append(bar(page, count, max_value))
    elif analytics_data:
        pages = analytics_data["pages"]
        lines.extend([
            "",
            "## Medicao propria do site",
            f"- Eventos coletados: {analytics_data['events']}",
            f"- Pageviews: {analytics_data['pageviews']}",
            f"- Sessoes aproximadas: {analytics_data['sessions']}",
            f"- Tempo medio aproximado por pagina: {analytics_data['avg_elapsed']:.0f}s",
            "",
            "Paginas mais acessadas:",
        ])
        max_value = max(pages.values()) if pages else 0
        for page, count in pages.most_common(10):
            lines.append(bar(page, count, max_value))
        if analytics_data["referrers"]:
            lines.extend(["", "Origens/referrers:"])
            for referrer, count in analytics_data["referrers"].most_common(8):
                lines.append(f"- {referrer}: {count}")
        if analytics_data["languages"]:
            lines.extend(["", "Idiomas do navegador:"])
            for language, count in analytics_data["languages"].most_common(5):
                lines.append(f"- {language}: {count}")
        if analytics_data["timezones"]:
            lines.extend(["", "Fusos/zonas informadas pelo navegador:"])
            for zone, count in analytics_data["timezones"].most_common(5):
                lines.append(f"- {zone}: {count}")
    else:
        lines.extend([
            "",
            "## Dados reais de audiencia",
            f"Pasta de logs configurada em {log_path_value}, mas ainda nao ha arquivos de log legiveis nela." if log_path_value else "Nenhum log local foi configurado em HOSTINGER_ACCESS_LOG_PATH.",
        ])
        if analytics_download_error:
            lines.append(analytics_download_error)

    if gsc_lines:
        lines.extend(["", "## Google Search Console", *gsc_lines])
    elif gsc_error:
        lines.extend(["", "## Google Search Console", gsc_error])

    missing = missing_sources()
    if missing:
        lines.extend(["", "## Conexoes pendentes"])
        for name, needed, impact in missing:
            lines.append(f"- {name}: configurar {needed}. Impacto: libera {impact}.")

    next_actions = []
    if sources.get("Google Search Console API"):
        next_actions.append("Acompanhar semanalmente consultas, CTR e paginas indexadas no Search Console.")
    else:
        next_actions.append("Conectar Search Console API para transformar buscas reais em pautas.")
    if analytics_data:
        next_actions.append("Revisar as paginas mais acessadas e criar links internos para manter o leitor no blog.")
    else:
        next_actions.append("Conectar GA4 ou logs de acesso para medir tempo, retencao, origem, geografia e dispositivos.")
    if gsc_lines and any("sem consultas" in line for line in gsc_lines):
        next_actions.append("Aguardar o processamento do sitemap e novas impressoes antes de pedir nova revisao do AdSense.")
    elif sources.get("Google AdSense"):
        next_actions.append("Revisar conteudo, datas, titulos e paginas institucionais antes de solicitar nova revisao do AdSense.")
    elif sources.get("Hostinger access logs"):
        next_actions.append("Usar logs da Hostinger para validar 404, paginas lentas e acessos que nao aparecem no analytics proprio.")
    else:
        next_actions.append("Exportar ou apontar logs da Hostinger para validar acessos, 404 e paginas acessadas sem depender de cookies.")

    lines.extend([
        "",
        "## O que esses numeros significam",
        "- Usuarios/sessoes mostram tamanho de audiencia e frequencia de visitas.",
        "- Tempo medio e engajamento mostram se o leitor fica no texto ou abandona rapido.",
        "- Origem de trafego mostra como as pessoas descobriram o blog.",
        "- Consultas do Search Console mostram as perguntas reais que trouxeram leitores.",
        "- Paginas de entrada e saida indicam quais textos atraem e onde a leitura termina.",
        "",
        "## Proximas acoes editoriais",
    ])
    lines.extend(f"{idx}. {action}" for idx, action in enumerate(next_actions, 1))

    telegram = "\n".join([
        "Verbo Vivo - resumo editorial",
        f"Fontes OK: {sum(1 for ok in sources.values() if ok)}/{len(sources)}",
        f"Artigos locais: {len(articles)}",
        "Search Console: conectado" if gsc_lines and not gsc_error else "Search Console: pendente/erro",
        f"Pageviews proprios: {analytics_data['pageviews']}" if analytics_data else (f"Paginas com log: {len(page_counts)}" if page_counts else "Dados de audiencia: pendentes"),
        f"Proxima acao: {next_actions[0]}",
    ])
    return "\n".join(lines), telegram


def send_telegram(text: str) -> str:
    token = env("TELEGRAM_BOT_TOKEN") or env("TELEGRAM_TOKEN")
    chat_id = env("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return send_telegram_via_github(text)
    payload = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    request = urllib.request.Request(url, data=payload, method="POST")
    with urllib.request.urlopen(request, timeout=20) as response:
        return f"Telegram enviado: HTTP {response.status}"


def send_telegram_via_github(text: str) -> str:
    repo = env("TELEGRAM_GH_REPO")
    workflow = env("TELEGRAM_GH_WORKFLOW")
    if not repo or not workflow:
        return "Telegram pendente: configure TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID ou TELEGRAM_GH_REPO/TELEGRAM_GH_WORKFLOW."
    token = env("GITHUB_TOKEN_FOR_TELEGRAM")
    if not token:
        return "Telegram pendente: GITHUB_TOKEN_FOR_TELEGRAM nao configurado para acionar GitHub Actions."
    payload = json.dumps({
        "ref": "main",
        "inputs": {"message": text[:12000]},
    }).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/dispatches",
        data=payload,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "verbo-vivo-audience-report",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status not in {200, 204}:
                return f"Falha ao acionar Telegram via GitHub: HTTP {response.status}"
    except Exception as exc:
        return f"Falha ao acionar Telegram via GitHub: {exc}"
    return f"Telegram acionado via GitHub Actions em {repo}/{workflow}."


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera relatorio editorial de audiencia do Verbo Vivo.")
    parser.add_argument("--authorize-search-console", action="store_true", help="Autoriza o Search Console por OAuth e salva token local.")
    parser.add_argument("--telegram", action="store_true", help="Envia o resumo curto ao Telegram se as credenciais existirem.")
    args = parser.parse_args()

    if args.authorize_search_console:
        print(authorize_search_console())
        return

    report, telegram = build_report()
    print(report)
    print("\n## Versao curta para Telegram\n")
    print(telegram)
    if args.telegram:
        print("\n" + send_telegram(telegram))


if __name__ == "__main__":
    main()
