<?php
declare(strict_types=1);

const CONFIG_FILE = __DIR__ . '/_private/editorial-config.php';
const DRAFT_DIR = __DIR__ . '/_editorial_drafts';
const AUTH_DIR = __DIR__ . '/_sender_authorizations';
const IMAGE_DIR = __DIR__ . '/images/articles';
const CRON_LOG_FILE = __DIR__ . '/_private/cron-editorial.log';

function esc(string $value): string {
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function row(string $label, bool $ok, string $detail = ''): string {
    return '<tr><th>' . esc($label) . '</th><td class="' . ($ok ? 'ok' : 'fail') . '">' . ($ok ? 'OK' : 'FALHA') . '</td><td>' . esc($detail) . '</td></tr>';
}

if (!is_file(CONFIG_FILE)) {
    http_response_code(500);
    exit('Configuracao privada ausente.');
}

$config = require CONFIG_FILE;
$token = $_GET['token'] ?? '';
$expected = (string) ($config['admin_token'] ?? '');
if (!is_string($token) || $expected === '' || !hash_equals($expected, $token)) {
    http_response_code(404);
    exit('Pagina nao encontrada.');
}

$rows = [];
$rows[] = row('PHP SAPI', true, php_sapi_name());
$rows[] = row('Versao do PHP', true, PHP_VERSION);
$rows[] = row('Arquivo privado de configuracao', is_file(CONFIG_FILE), CONFIG_FILE);
$rows[] = row('Funcao imap_open', function_exists('imap_open'), function_exists('imap_open') ? 'Extensao IMAP ativa.' : 'Extensao IMAP ausente. O cron nao consegue ler e-mails.');
$rows[] = row('Funcao curl_init', function_exists('curl_init'), function_exists('curl_init') ? 'cURL ativo.' : 'Sem cURL; chamadas externas podem falhar.');
$rows[] = row('Funcao mail', function_exists('mail'), function_exists('mail') ? 'mail() disponivel.' : 'mail() indisponivel.');

foreach ([DRAFT_DIR, AUTH_DIR, IMAGE_DIR] as $dir) {
    if (!is_dir($dir)) {
        @mkdir($dir, 0755, true);
    }
    $rows[] = row('Diretorio gravavel: ' . basename($dir), is_dir($dir) && is_writable($dir), $dir);
}

$required = [
    'editorial_imap_host',
    'editorial_imap_port',
    'editorial_imap_user',
    'editorial_imap_password',
    'editorial_smtp_user',
    'editorial_smtp_password',
    'publish_imap_host',
    'publish_imap_port',
    'publish_imap_user',
    'publish_imap_password',
    'openai_api_key',
    'admin_token',
];
foreach ($required as $key) {
    $value = (string) ($config[$key] ?? '');
    $rows[] = row('Config: ' . $key, $value !== '', $value !== '' ? 'Presente' : 'Vazio');
}

if (function_exists('imap_open')) {
    $mailboxes = [
        'artigo@' => ['editorial_imap_host', 'editorial_imap_port', 'editorial_imap_user', 'editorial_imap_password'],
        'publicar@' => ['publish_imap_host', 'publish_imap_port', 'publish_imap_user', 'publish_imap_password'],
    ];
    foreach ($mailboxes as $label => $keys) {
        [$hostKey, $portKey, $userKey, $passwordKey] = $keys;
        $mailbox = sprintf('{%s:%d/imap/ssl}INBOX', (string) $config[$hostKey], (int) $config[$portKey]);
        $imap = @imap_open($mailbox, (string) $config[$userKey], (string) $config[$passwordKey]);
        if ($imap) {
            $unseen = imap_search($imap, 'UNSEEN') ?: [];
            $rows[] = row('Login IMAP ' . $label, true, count($unseen) . ' mensagem(ns) nao lida(s).');
            imap_close($imap);
        } else {
            $rows[] = row('Login IMAP ' . $label, false, (string) imap_last_error());
        }
    }
}

$logHtml = '<p>Nenhum log gravado ainda.</p>';
if (is_file(CRON_LOG_FILE)) {
    $lines = file(CRON_LOG_FILE, FILE_IGNORE_NEW_LINES) ?: [];
    $tail = array_slice($lines, -30);
    $logHtml = '<pre>' . esc(implode("\n", $tail)) . '</pre>';
}

echo '<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Diagnostico do cron | Verbo Vivo</title>
    <style>
      body{font-family:Arial,Helvetica,sans-serif;background:#fbfaf6;color:#17201b;margin:0;padding:32px}
      main{max-width:980px;margin:auto;background:#fffdf8;border:1px solid #d8d0bf;padding:28px}
      table{border-collapse:collapse;width:100%;margin-top:22px}
      th,td{border-bottom:1px solid #d8d0bf;padding:10px;text-align:left;vertical-align:top}
      th{width:250px}.ok{color:#1f6f43;font-weight:800}.fail{color:#9b2d20;font-weight:800}
      pre{background:#17201b;color:#fbfaf6;overflow:auto;padding:16px;white-space:pre-wrap}
      code{background:#f2ede1;padding:2px 5px}
    </style>
  </head>
  <body>
    <main>
      <p><strong>Verbo Vivo</strong></p>
      <h1>Diagnostico do cron editorial</h1>
      <p>Esta pagina nao processa artigos. Ela apenas verifica ambiente, configuracao e conexao IMAP.</p>
      <table><tbody>' . implode('', $rows) . '</tbody></table>
      <h2>Ultimas linhas do log do cron</h2>
      ' . $logHtml . '
    </main>
  </body>
</html>';
