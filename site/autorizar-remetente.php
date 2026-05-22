<?php
declare(strict_types=1);

const AUTH_DIR = __DIR__ . '/_sender_authorizations';
const PRIVATE_DIR = __DIR__ . '/_private';
const ALLOWLIST_FILE = PRIVATE_DIR . '/allowed-senders.json';
const TEMP_ALLOWLIST_FILE = PRIVATE_DIR . '/temporary-sender-authorizations.json';

function esc(string $value): string {
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function load_json(string $path): array {
    if (!is_file($path)) {
        return [];
    }
    $data = json_decode((string) file_get_contents($path), true);
    return is_array($data) ? $data : [];
}

function save_json(string $path, array $data): void {
    if (!is_dir(dirname($path))) {
        mkdir(dirname($path), 0755, true);
    }
    file_put_contents($path, json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
}

function normalize_email(string $email): string {
    return strtolower(trim($email));
}

function page(string $title, string $message): void {
    echo '<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>' . esc($title) . ' | Verbo Vivo</title>
    <link rel="stylesheet" href="styles.css" />
    <style>
      .auth-wrap { margin: 0 auto; max-width: 760px; padding: clamp(36px, 8vw, 96px) clamp(18px, 4vw, 48px); }
      .auth-box { background: var(--white); border: 1px solid var(--line); box-shadow: var(--shadow); padding: clamp(22px, 4vw, 38px); }
      .auth-box p { color: var(--muted); font-size: 1.05rem; line-height: 1.7; }
    </style>
  </head>
  <body>
    <header class="site-header">
      <a class="brand" href="index.html"><span class="brand-mark">VV</span><span><strong>Verbo Vivo</strong><small>verbovivo.blog</small></span></a>
      <nav aria-label="Navegacao principal"><a href="index.html#artigos">Artigos</a><a href="sobre.html">Sobre</a><a href="contato.html">Contato</a><a href="faq.html">FAQ</a></nav>
    </header>
    <main class="auth-wrap"><section class="auth-box"><p class="eyebrow">Seguranca editorial</p><h1>' . esc($title) . '</h1><p>' . esc($message) . '</p></section></main>
  </body>
</html>';
}

$token = $_GET['token'] ?? '';
$mode = $_GET['mode'] ?? '';
if (!is_string($token) || !preg_match('/^[A-Za-z0-9_-]{20,}$/', $token)) {
    http_response_code(400);
    page('Token invalido', 'O link de autorizacao esta invalido.');
    exit;
}
if (!is_string($mode) || !in_array($mode, ['temporary', 'permanent'], true)) {
    http_response_code(400);
    page('Modo invalido', 'Escolha uma autorizacao temporaria ou permanente.');
    exit;
}

$pendingPath = AUTH_DIR . '/' . $token . '.json';
if (!is_file($pendingPath)) {
    http_response_code(404);
    page('Pedido nao encontrado', 'Esse pedido de autorizacao nao foi encontrado ou ja foi removido.');
    exit;
}

$pending = load_json($pendingPath);
$sender = normalize_email((string) ($pending['sender'] ?? ''));
$messageKey = (string) ($pending['message_key'] ?? '');
if ($sender === '' || $messageKey === '') {
    http_response_code(500);
    page('Pedido incompleto', 'Esse pedido nao possui os dados necessarios para autorizacao.');
    exit;
}

if ($mode === 'permanent') {
    $allowed = array_values(array_unique(array_map('normalize_email', load_json(ALLOWLIST_FILE))));
    if (!in_array($sender, $allowed, true)) {
        $allowed[] = $sender;
        sort($allowed);
        save_json(ALLOWLIST_FILE, $allowed);
    }
    @unlink($pendingPath);
    page('Remetente autorizado', 'O remetente ' . $sender . ' foi autorizado permanentemente. O agente processara as mensagens desse remetente no proximo ciclo.');
    exit;
}

$temporary = load_json(TEMP_ALLOWLIST_FILE);
$temporary[$messageKey] = [
    'sender' => $sender,
    'expires_at' => gmdate(DATE_ATOM, time() + 86400),
    'authorized_at' => gmdate(DATE_ATOM),
];
save_json(TEMP_ALLOWLIST_FILE, $temporary);
@unlink($pendingPath);
page('Mensagem autorizada', 'Apenas esta mensagem de ' . $sender . ' foi autorizada por 24 horas. O agente processara essa mensagem no proximo ciclo.');

