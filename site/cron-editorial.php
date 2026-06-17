<?php
declare(strict_types=1);

const DOMAIN = 'https://verbovivo.blog';
const DRAFT_DIR = __DIR__ . '/_editorial_drafts';
const AUTH_DIR = __DIR__ . '/_sender_authorizations';
const ARTICLE_DIR = __DIR__ . '/artigos';
const IMAGE_DIR = __DIR__ . '/images/articles';
const CONFIG_FILE = __DIR__ . '/_private/editorial-config.php';
const ALLOWLIST_FILE = __DIR__ . '/_private/allowed-senders.json';
const TEMP_ALLOWLIST_FILE = __DIR__ . '/_private/temporary-sender-authorizations.json';
const CRON_LOG_FILE = __DIR__ . '/_private/cron-editorial.log';
const DEFAULT_AUTHOR = 'Pastor AntÃ´nio Lemos';
const DEFAULT_AUTHOR_SOCIALS = [
    'instagram' => 'https://www.instagram.com/antoniolemosoficial/',
    'youtube' => 'https://www.youtube.com/@Lemos3',
    'facebook' => 'https://www.facebook.com/PastorAntonioLemos',
];

if (!function_exists('str_contains')) {
    function str_contains(string $haystack, string $needle): bool {
        return $needle === '' || strpos($haystack, $needle) !== false;
    }
}

if (!function_exists('str_starts_with')) {
    function str_starts_with(string $haystack, string $needle): bool {
        return $needle === '' || strncmp($haystack, $needle, strlen($needle)) === 0;
    }
}

if (!function_exists('str_ends_with')) {
    function str_ends_with(string $haystack, string $needle): bool {
        if ($needle === '') {
            return true;
        }
        $length = strlen($needle);
        return substr($haystack, -$length) === $needle;
    }
}

if (!is_file(CONFIG_FILE)) {
    fwrite(STDERR, "Missing private config.\n");
    exit(1);
}

$config = require CONFIG_FILE;
if (php_sapi_name() !== 'cli') {
    http_response_code(403);
    exit('Forbidden');
}

function vv_log(string $message): void {
    $line = '[' . gmdate('c') . '] ' . $message . PHP_EOL;
    echo $line;
    @file_put_contents(CRON_LOG_FILE, $line, FILE_APPEND | LOCK_EX);
}

function esc(string $value): string {
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function slugify(string $value): string {
    $value = iconv('UTF-8', 'ASCII//TRANSLIT//IGNORE', $value) ?: $value;
    $value = strtolower((string) preg_replace('/[^a-zA-Z0-9]+/', '-', $value));
    $value = trim($value, '-');
    return $value !== '' ? $value : bin2hex(random_bytes(4));
}

function key_normalize(string $value): string {
    $value = iconv('UTF-8', 'ASCII//TRANSLIT//IGNORE', $value) ?: $value;
    return strtolower(trim($value));
}

function normalize_social_url(string $value): string {
    $value = trim($value);
    if ($value === '' || str_starts_with($value, '@')) {
        return $value;
    }
    return preg_match('/^https?:\/\//i', $value) ? $value : 'https://' . $value;
}

function extract_submission_metadata(string $source): array {
    $metadata = ['author' => '', 'guest_author' => false, 'socials' => []];
    $body = [];
    $inHeader = true;
    foreach (preg_split('/\R/', $source) as $line) {
        $clean = trim($line);
        if ($inHeader && $clean === '') {
            $inHeader = false;
            $body[] = $line;
            continue;
        }
        if ($inHeader && str_contains($clean, ':')) {
            [$key, $value] = explode(':', $clean, 2);
            $key = key_normalize($key);
            $value = trim($value);
            if (in_array($key, ['autor convidado', 'author guest', 'guest author'], true)) {
                $metadata['author'] = $value;
                $metadata['guest_author'] = $value !== '';
                continue;
            }
            if (in_array($key, ['autor', 'author', 'nome', 'nome do autor'], true)) {
                continue;
            }
            if (in_array($key, ['instagram', 'facebook', 'youtube', 'x', 'twitter', 'linkedin', 'site', 'website'], true)) {
                if ($value !== '') {
                    $metadata['socials'][$key] = normalize_social_url($value);
                }
                continue;
            }
        }
        $body[] = $line;
    }
    $article = trim(implode("\n", $body));
    return [$metadata, $article !== '' ? $article : trim($source)];
}

function submission_author(array $metadata): string {
    return !empty($metadata['guest_author']) ? (string) $metadata['author'] : DEFAULT_AUTHOR;
}

function submission_socials(array $metadata): array {
    return !empty($metadata['guest_author']) ? $metadata['socials'] : DEFAULT_AUTHOR_SOCIALS;
}

function social_label(string $name): string {
    return [
        'instagram' => 'Instagram',
        'facebook' => 'Facebook',
        'youtube' => 'YouTube',
        'x' => 'X',
        'twitter' => 'X',
        'linkedin' => 'LinkedIn',
        'site' => 'Site',
        'website' => 'Site',
    ][$name] ?? ucfirst($name);
}

function social_icon(string $name): string {
    $icons = [
        'instagram' => '<svg class="social-icon social-icon--instagram" aria-hidden="true" viewBox="0 0 24 24"><path d="M7.8 2h8.4C19.4 2 22 4.6 22 7.8v8.4c0 3.2-2.6 5.8-5.8 5.8H7.8C4.6 22 2 19.4 2 16.2V7.8C2 4.6 4.6 2 7.8 2Zm-.2 2A3.6 3.6 0 0 0 4 7.6v8.8C4 18.39 5.61 20 7.6 20h8.8c1.99 0 3.6-1.61 3.6-3.6V7.6C20 5.61 18.39 4 16.4 4H7.6Zm9.65 1.5a1.25 1.25 0 1 1 0 2.5 1.25 1.25 0 0 1 0-2.5ZM12 7a5 5 0 1 1 0 10 5 5 0 0 1 0-10Zm0 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z"/></svg>',
        'facebook' => '<svg class="social-icon social-icon--facebook" aria-hidden="true" viewBox="0 0 24 24"><path d="M13.45 23.69v-7.98h3.25l.67-3.67h-3.92v-1.3c0-1.94.76-2.68 2.73-2.68.61 0 1.1.02 1.39.05V4.79c-.54-.15-1.85-.3-2.61-.3-4.01 0-5.86 1.89-5.86 5.98v1.58H6.63v3.67H9.1v7.98h4.35Z"/></svg>',
        'youtube' => '<svg class="social-icon social-icon--youtube" aria-hidden="true" viewBox="0 0 24 24"><path d="M23.5 6.19a3.02 3.02 0 0 0-2.12-2.14C19.5 3.55 12 3.55 12 3.55s-7.5 0-9.38.5A3.02 3.02 0 0 0 .5 6.19C0 8.08 0 12 0 12s0 3.92.5 5.81a3.02 3.02 0 0 0 2.12 2.14c1.88.5 9.38.5 9.38.5s7.5 0 9.38-.5a3.02 3.02 0 0 0 2.12-2.14C24 15.92 24 12 24 12s0-3.92-.5-5.81ZM9.55 15.57V8.43L15.82 12l-6.27 3.57Z"/></svg>',
        'x' => '<svg class="social-icon social-icon--x" aria-hidden="true" viewBox="0 0 24 24"><path d="M18.9 1.15h3.68l-8.04 9.19L24 22.85h-7.41l-5.8-7.59-6.64 7.59H.47l8.6-9.83L0 1.15h7.59l5.24 6.93 6.07-6.93Zm-1.29 19.49h2.04L6.48 3.24H4.29l13.32 17.4Z"/></svg>',
        'twitter' => '<svg class="social-icon social-icon--x" aria-hidden="true" viewBox="0 0 24 24"><path d="M18.9 1.15h3.68l-8.04 9.19L24 22.85h-7.41l-5.8-7.59-6.64 7.59H.47l8.6-9.83L0 1.15h7.59l5.24 6.93 6.07-6.93Zm-1.29 19.49h2.04L6.48 3.24H4.29l13.32 17.4Z"/></svg>',
        'linkedin' => '<svg class="social-icon social-icon--linkedin" aria-hidden="true" viewBox="0 0 24 24"><path d="M20.45 20.45h-3.55v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28ZM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13Zm1.78 13.02H3.56V9h3.56v11.45ZM22.22 0H1.77C.79 0 0 .77 0 1.72v20.56C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.72V1.72C24 .77 23.2 0 22.22 0Z"/></svg>',
        'site' => '<svg class="social-icon social-icon--site" aria-hidden="true" viewBox="0 0 24 24"><path d="M14 3h7v7h-2V6.41l-9.29 9.3-1.42-1.42 9.3-9.29H14V3ZM5 5h6v2H7v10h10v-4h2v6H5V5Z"/></svg>',
        'website' => '<svg class="social-icon social-icon--site" aria-hidden="true" viewBox="0 0 24 24"><path d="M14 3h7v7h-2V6.41l-9.29 9.3-1.42-1.42 9.3-9.29H14V3ZM5 5h6v2H7v10h10v-4h2v6H5V5Z"/></svg>',
    ];
    return $icons[$name] ?? $icons['site'];
}

function author_socials_html(array $socials): string {
    $links = [];
    foreach ($socials as $name => $url) {
        $href = (string) $url;
        if (str_starts_with($href, '@')) {
            $handle = ltrim($href, '@');
            if ($name === 'instagram') {
                $href = 'https://instagram.com/' . $handle;
            } elseif ($name === 'x' || $name === 'twitter') {
                $href = 'https://x.com/' . $handle;
            }
        }
        $label = social_label((string) $name);
        $links[] = '<a href="' . esc($href) . '" target="_blank" rel="noopener" aria-label="' . esc($label) . '" title="' . esc($label) . '">' . social_icon((string) $name) . '</a>';
    }
    return $links ? '<div class="author-socials" aria-label="Redes sociais do autor">' . implode('', $links) . '</div>' : '';
}

function openai_json(array $config, array $payload): array {
    $body = json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    $headers = [
        'Content-Type: application/json',
        'Authorization: Bearer ' . $config['openai_api_key'],
    ];
    if (function_exists('curl_init')) {
        $ch = curl_init('https://api.openai.com/v1/chat/completions');
        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => $body,
            CURLOPT_HTTPHEADER => $headers,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 90,
        ]);
        $raw = curl_exec($ch);
        if ($raw === false) {
            throw new RuntimeException('OpenAI chat failed: ' . curl_error($ch));
        }
        curl_close($ch);
    } else {
        $raw = file_get_contents('https://api.openai.com/v1/chat/completions', false, stream_context_create([
            'http' => [
                'method' => 'POST',
                'header' => implode("\r\n", $headers),
                'content' => $body,
                'timeout' => 90,
            ],
        ]));
        if ($raw === false) {
            throw new RuntimeException('OpenAI chat failed.');
        }
    }
    $data = json_decode($raw, true);
    if (!is_array($data)) {
        throw new RuntimeException('Invalid OpenAI chat response.');
    }
    return $data;
}

function openai_image(array $config, string $prompt, string $outputPath): bool {
    $payload = [
        'model' => 'gpt-image-1',
        'prompt' => 'Crie uma imagem editorial cristã premium para o blog Verbo Vivo, com aparência viva, nítida e realista, semelhante às melhores imagens enviadas prontas para publicação: cores ricas e naturais, contraste bem definido, luz cinematográfica quente, textura visível, profundidade de campo controlada e composição limpa. Priorize cenas simbólicas cristãs com paisagens reais, caminhos, luz natural, céu dramático, pedras, oliveiras, madeira, pergaminho, arquitetura antiga, mãos em oração quando fizer sentido, sempre com atmosfera reverente e esperançosa. A imagem não pode parecer leitosa, embaçada, lavada, genérica, infantil, caricata, aquarela, pintura borrada, baixa resolução, stock artificial ou ilustração sem vida. Não inclua texto escrito, letras, marcas, logotipos, versículos na imagem, rostos em close, representação literal de Jesus, mãos deformadas ou elementos exageradamente clichês. Use enquadramento horizontal editorial 3:2, sujeito claro, fundo harmonioso e qualidade visual pronta para capa de artigo. Contexto bíblico/reflexivo para orientar a cena: ' . $prompt,
        'size' => '1536x1024',
    ];
    $body = json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    $headers = [
        'Content-Type: application/json',
        'Authorization: Bearer ' . $config['openai_api_key'],
    ];
    $ch = curl_init('https://api.openai.com/v1/images/generations');
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $body,
        CURLOPT_HTTPHEADER => $headers,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 180,
    ]);
    $raw = curl_exec($ch);
    if ($raw === false) {
        vv_log('Image generation failed: ' . curl_error($ch));
        curl_close($ch);
        return false;
    }
    curl_close($ch);
    $data = json_decode($raw, true);
    $b64 = $data['data'][0]['b64_json'] ?? '';
    if (!is_string($b64) || $b64 === '') {
        vv_log('Image generation returned no image.');
        return false;
    }
    file_put_contents($outputPath, base64_decode($b64));
    return true;
}

function extract_body($imap, int $msgNo): string {
    $plain = imap_fetchbody($imap, $msgNo, '1.1') ?: imap_fetchbody($imap, $msgNo, '1') ?: '';
    $html = imap_fetchbody($imap, $msgNo, '1.2') ?: imap_fetchbody($imap, $msgNo, '2') ?: '';
    $text = quoted_printable_decode(base64_decode($plain, true) !== false ? base64_decode($plain) : $plain);
    if (trim($text) !== '') {
        return trim(strip_tags($text));
    }
    $htmlText = quoted_printable_decode(base64_decode($html, true) !== false ? base64_decode($html) : $html);
    return trim(strip_tags($htmlText));
}

function smtp_read($socket): string {
    $response = '';
    while (($line = fgets($socket, 515)) !== false) {
        $response .= $line;
        if (strlen($line) >= 4 && $line[3] === ' ') {
            break;
        }
    }
    return $response;
}

function smtp_expect($socket, array $codes, string $context): string {
    $response = smtp_read($socket);
    $code = (int) substr($response, 0, 3);
    if (!in_array($code, $codes, true)) {
        throw new RuntimeException($context . ' failed: ' . trim($response));
    }
    return $response;
}

function smtp_command($socket, string $command, array $codes, string $context): string {
    fwrite($socket, $command . "\r\n");
    return smtp_expect($socket, $codes, $context);
}

function smtp_send(array $config, string $to, string $subject, string $html, string $text): void {
    $boundary = 'vv_' . bin2hex(random_bytes(12));
    $from = (string) $config['editorial_smtp_user'];
    $subjectHeader = '=?UTF-8?B?' . base64_encode($subject) . '?=';
    $headers = implode("\r\n", [
        'From: Verbo Vivo <' . $from . '>',
        'To: ' . $to,
        'Subject: ' . $subjectHeader,
        'Date: ' . date(DATE_RFC2822),
        'MIME-Version: 1.0',
        'Content-Type: multipart/alternative; boundary="' . $boundary . '"',
    ]);
    $body = "--$boundary\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n" . chunk_split(base64_encode($text));
    $body .= "\r\n--$boundary\r\nContent-Type: text/html; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n" . chunk_split(base64_encode($html));
    $body .= "\r\n--$boundary--\r\n";
    $message = preg_replace('/^\./m', '..', $headers . "\r\n\r\n" . $body);

    $host = (string) $config['editorial_smtp_host'];
    $port = (int) $config['editorial_smtp_port'];
    $socket = fsockopen('ssl://' . $host, $port, $errno, $errstr, 30);
    if (!$socket) {
        throw new RuntimeException('SMTP connection failed: ' . $errstr . ' (' . $errno . ')');
    }
    stream_set_timeout($socket, 60);
    try {
        smtp_expect($socket, [220], 'SMTP greeting');
        smtp_command($socket, 'EHLO verbovivo.blog', [250], 'SMTP EHLO');
        smtp_command($socket, 'AUTH LOGIN', [334], 'SMTP auth start');
        smtp_command($socket, base64_encode((string) $config['editorial_smtp_user']), [334], 'SMTP auth user');
        smtp_command($socket, base64_encode((string) $config['editorial_smtp_password']), [235], 'SMTP auth password');
        smtp_command($socket, 'MAIL FROM:<' . $from . '>', [250], 'SMTP MAIL FROM');
        smtp_command($socket, 'RCPT TO:<' . $to . '>', [250, 251], 'SMTP RCPT TO');
        smtp_command($socket, 'DATA', [354], 'SMTP DATA');
        fwrite($socket, $message . "\r\n.\r\n");
        smtp_expect($socket, [250], 'SMTP message send');
        smtp_command($socket, 'QUIT', [221], 'SMTP QUIT');
    } finally {
        fclose($socket);
    }
}

function normalize_email(string $email): string {
    return strtolower(trim($email));
}

function json_file_array(string $path): array {
    if (!is_file($path)) {
        return [];
    }
    $data = json_decode((string) file_get_contents($path), true);
    return is_array($data) ? $data : [];
}

function save_json_file(string $path, array $data): void {
    if (!is_dir(dirname($path))) {
        mkdir(dirname($path), 0755, true);
    }
    file_put_contents($path, json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
}

function save_review_draft_file(array $draft): void {
    if (!is_dir(DRAFT_DIR)) {
        mkdir(DRAFT_DIR, 0755, true);
    }
    $json = json_encode($draft, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    if (!is_string($json) || trim($json) === '') {
        throw new RuntimeException('Draft JSON serialization failed.');
    }
    $target = DRAFT_DIR . '/' . $draft['token'] . '.json';
    $tmp = $target . '.tmp';
    $bytes = file_put_contents($tmp, $json, LOCK_EX);
    if ($bytes === false || $bytes < 20) {
        @unlink($tmp);
        throw new RuntimeException('Draft JSON write failed.');
    }
    if (!rename($tmp, $target)) {
        @unlink($tmp);
        throw new RuntimeException('Draft JSON rename failed.');
    }
}

function configured_allowed_senders(array $config): array {
    $raw = (string) ($config['allowed_senders'] ?? '');
    $items = preg_split('/[,;\s]+/', $raw) ?: [];
    $items[] = (string) ($config['approver_email'] ?? '');
    $items[] = 'hebergravano@gmail.com';
    $items = array_map('normalize_email', $items);
    return array_values(array_unique(array_filter($items)));
}

function permanent_allowed_senders(array $config): array {
    $stored = array_map('normalize_email', json_file_array(ALLOWLIST_FILE));
    return array_values(array_unique(array_merge(configured_allowed_senders($config), $stored)));
}

function message_key(string $flow, string $from, string $subject, string $messageId): string {
    return hash('sha256', normalize_email($flow) . '|' . normalize_email($from) . '|' . trim($subject) . '|' . trim($messageId));
}

function is_message_temporarily_authorized(string $key, string $from): bool {
    $temporary = json_file_array(TEMP_ALLOWLIST_FILE);
    $entry = $temporary[$key] ?? null;
    if (!is_array($entry)) {
        return false;
    }
    if (normalize_email((string) ($entry['sender'] ?? '')) !== normalize_email($from)) {
        return false;
    }
    $expires = strtotime((string) ($entry['expires_at'] ?? ''));
    return $expires !== false && $expires >= time();
}

function is_sender_authorized(array $config, string $flow, string $from, string $subject, string $messageId): bool {
    $sender = normalize_email($from);
    if (in_array($sender, permanent_allowed_senders($config), true)) {
        return true;
    }
    return is_message_temporarily_authorized(message_key($flow, $from, $subject, $messageId), $from);
}

function request_sender_authorization(array $config, string $flow, string $from, string $subject, string $messageId): void {
    $approver = trim((string) ($config['approver_email'] ?? ''));
    if ($approver === '') {
        vv_log('Unauthorized sender blocked but approver_email is not configured: ' . $from);
        return;
    }
    if (!is_dir(AUTH_DIR)) {
        mkdir(AUTH_DIR, 0755, true);
    }
    $key = message_key($flow, $from, $subject, $messageId);
    foreach (glob(AUTH_DIR . '/*.json') ?: [] as $path) {
        $pending = json_file_array($path);
        if (($pending['message_key'] ?? '') === $key) {
            vv_log('Authorization request already pending for ' . $from);
            return;
        }
    }
    $token = rtrim(strtr(base64_encode(random_bytes(24)), '+/', '-_'), '=');
    $payload = [
        'token' => $token,
        'message_key' => $key,
        'flow' => $flow,
        'sender' => normalize_email($from),
        'subject' => $subject,
        'message_id' => $messageId,
        'created_at' => gmdate(DATE_ATOM),
    ];
    save_json_file(AUTH_DIR . '/' . $token . '.json', $payload);
    $temporaryUrl = DOMAIN . '/autorizar-remetente.php?token=' . rawurlencode($token) . '&mode=temporary';
    $permanentUrl = DOMAIN . '/autorizar-remetente.php?token=' . rawurlencode($token) . '&mode=permanent';
    $html = '<div style="font-family:Arial,Helvetica,sans-serif;background:#fbfaf6;color:#17201b;padding:24px;">'
        . '<div style="max-width:680px;margin:0 auto;background:#fffdf8;border:1px solid #d8d0bf;padding:24px;">'
        . '<p style="color:#4f7059;font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;">Verbo Vivo</p>'
        . '<h1 style="font-family:Georgia,serif;">Autorizar novo remetente?</h1>'
        . '<p><strong>Remetente:</strong> ' . esc($from) . '</p>'
        . '<p><strong>Caixa:</strong> ' . esc($flow) . '</p>'
        . '<p><strong>Assunto:</strong> ' . esc($subject) . '</p>'
        . '<p>O agente bloqueou este envio porque o remetente ainda nao esta na lista aprovada. Escolha uma autorizacao:</p>'
        . '<p><a href="' . esc($temporaryUrl) . '" style="display:inline-block;background:#a9792e;color:#fffdf8;text-decoration:none;font-weight:800;padding:13px 18px;margin:0 10px 10px 0;">Autorizar somente este artigo</a>'
        . '<a href="' . esc($permanentUrl) . '" style="display:inline-block;background:#4f7059;color:#fffdf8;text-decoration:none;font-weight:800;padding:13px 18px;">Autorizar remetente permanente</a></p>'
        . '</div></div>';
    $text = "Autorizar novo remetente?\n\nRemetente: $from\nCaixa: $flow\nAssunto: $subject\n\nTemporario: $temporaryUrl\nPermanente: $permanentUrl\n";
    smtp_send($config, $approver, 'Autorizar remetente no Verbo Vivo: ' . $from, $html, $text);
    vv_log('Authorization request sent for ' . $from);
}

function email_preview(array $draft): string {
    $reviewUrl = DOMAIN . '/revisao.php?token=' . rawurlencode((string) $draft['token']);
    $image = (string) ($draft['image_filename'] ?? '');
    $imageHtml = $image !== '' ? '<img src="' . DOMAIN . '/images/articles/' . esc($image) . '" alt="' . esc((string) $draft['title']) . '" style="display:block;width:100%;max-width:720px;border:1px solid #d8d0bf;margin:18px 0;" />' : '';
    return '<div style="background:#fbfaf6;color:#17201b;font-family:Arial,Helvetica,sans-serif;padding:24px;"><div style="max-width:760px;margin:0 auto;background:#fffdf8;border:1px solid #d8d0bf;padding:24px;"><p style="color:#4f7059;font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;margin:0 0 10px;">Verbo Vivo</p><h1 style="font-family:Georgia,serif;font-size:34px;line-height:1.05;margin:0 0 12px;">' . esc((string) $draft['title']) . '</h1><p style="color:#59645c;font-size:16px;line-height:1.6;margin:0 0 14px;">' . esc((string) $draft['excerpt']) . '</p><p style="color:#a9792e;font-weight:800;margin:0 0 8px;">Por ' . esc((string) $draft['author']) . '</p>' . author_socials_html($draft['author_socials'] ?? []) . $imageHtml . '<div style="font-family:Georgia,serif;color:#2d3831;font-size:17px;line-height:1.75;">' . (string) $draft['body_html'] . '</div><div style="border-top:1px solid #d8d0bf;margin-top:26px;padding-top:20px;"><a href="' . $reviewUrl . '#aprovar" style="display:inline-block;background:#4f7059;color:#fffdf8;text-decoration:none;font-weight:800;padding:13px 18px;margin:0 10px 10px 0;">Aprovar e publicar</a><a href="' . $reviewUrl . '#corrigir" style="display:inline-block;background:#a9792e;color:#fffdf8;text-decoration:none;font-weight:800;padding:13px 18px;">Corrigir antes de publicar</a></div></div></div>';
}

function plain_text(string $value): string {
    $value = strip_tags($value);
    return trim((string) preg_replace('/\s+/', ' ', $value));
}

function trim_sentence(string $value, int $limit): string {
    $value = plain_text($value);
    if (strlen($value) <= $limit) {
        return $value;
    }
    $cut = substr($value, 0, $limit - 1);
    $cut = (string) preg_replace('/\s+\S*$/u', '', $cut);
    return rtrim($cut, " ,.;:\t\n\r\0\x0B") . '.';
}

function normalize_direct_submission_text(string $text): string {
    $text = str_replace(["\r\n", "\r"], "\n", $text);
    $kept = [];
    foreach (preg_split('/\n/', $text) as $line) {
        $clean = trim((string) $line);
        $clean = (string) preg_replace('/^corpo\s+do\s+e-?mail:\s*/iu', '', $clean);
        if ($clean === '') {
            $kept[] = '';
            continue;
        }
        $discard = [
            '/^\[image:\s*.*?\]$/iu',
            '/^!\[.*?\]\(.*?\)$/u',
            '/^texto(?:\s+mais\s+imagem)?\s+do\s+artigo\s+come[cÃ§]a\s+aqui\.{0,3}$/iu',
            '/^assunto\s+do\s+e-?mail:/iu',
            '/^[-_]{3,}$/u',
            '/^(?:enviado|sent)\s+(?:do|from)\s+meu\b/iu',
            '/^(?:de|from|para|to|assunto|subject|data|date):\s/iu',
        ];
        $skip = false;
        foreach ($discard as $pattern) {
            if (preg_match($pattern, $clean)) {
                $skip = true;
                break;
            }
        }
        if (!$skip) {
            $kept[] = $clean;
        }
    }
    return trim((string) preg_replace("/\n{3,}/", "\n\n", implode("\n", $kept)));
}

function paragraphs_from_text(string $text): array {
    $blocks = array_values(array_filter(array_map('trim', preg_split("/\n\s*\n/", $text) ?: [])));
    if (count($blocks) <= 1) {
        $blocks = array_values(array_filter(array_map('trim', preg_split('/\R/', $text) ?: [])));
    }
    return $blocks;
}

function normalized_heading(string $value): string {
    return key_normalize(rtrim(trim($value, "*# \t\n\r\0\x0B"), ':'));
}

function split_direct_references(string $text): array {
    $headings = ['fontes', 'fontes e dicionarios de referencia', 'referencias', 'referencias bibliograficas', 'bibliografia'];
    $main = [];
    $refs = [];
    $inRefs = false;
    foreach (preg_split('/\R/', $text) as $line) {
        if (in_array(normalized_heading((string) $line), $headings, true)) {
            $inRefs = true;
            continue;
        }
        $inRefs ? $refs[] = $line : $main[] = $line;
    }
    return [trim(implode("\n", $main)), trim(implode("\n", $refs))];
}

function inline_direct_markup(string $text): string {
    $text = (string) preg_replace_callback(
        '/\b([1-3]?\s?[\p{Lu}][\p{L}]+)\s+(\d{1,3}):(\d{1,3})(?:-(\d{1,3}))?/u',
        function (array $match): string {
            $book = trim((string) preg_replace('/\s+/', ' ', $match[1]));
            if (isset($match[4]) && $match[4] !== '') {
                return $book . ', capÃ­tulo ' . $match[2] . ', versÃ­culos ' . $match[3] . ' a ' . $match[4];
            }
            return $book . ', capÃ­tulo ' . $match[2] . ', versÃ­culo ' . $match[3];
        },
        $text
    );
    $value = esc(trim($text));
    $value = (string) preg_replace('/\*\*(.+?)\*\*/s', '<strong>$1</strong>', $value);
    return (string) preg_replace('/\*(.+?)\*/s', '<em>$1</em>', $value);
}

function looks_like_direct_heading(string $text): bool {
    $clean = trim($text, "*# \t\n\r\0\x0B");
    if ($clean === '' || strlen($clean) > 120 || preg_match('/[.!?;:]$/u', $clean)) {
        return false;
    }
    $words = preg_split('/\s+/', $clean) ?: [];
    if (count($words) < 2 || count($words) > 12) {
        return false;
    }
    $first = substr((string) $words[0], 0, 1);
    return strtoupper($first) === $first;
}

function direct_references_html(string $text): string {
    if (trim($text) === '') {
        return '';
    }
    $items = [];
    $current = [];
    foreach (preg_split('/\R/', $text) as $line) {
        $clean = trim((string) $line);
        if ($clean === '') {
            continue;
        }
        if (str_starts_with($clean, '- ')) {
            if ($current) {
                $items[] = implode(' ', $current);
            }
            $current = [trim(substr($clean, 2))];
        } else {
            $current[] = $clean;
        }
    }
    if ($current) {
        $items[] = implode(' ', $current);
    }
    if (!$items) {
        $items[] = trim($text);
    }
    $rendered = '';
    foreach ($items as $item) {
        $rendered .= '<li>' . inline_direct_markup((string) $item) . '</li>';
    }
    return '<aside class="article-references" aria-label="ReferÃªncias para aprofundamento"><h2>Para aprofundar a leitura</h2><p>Estas obras podem ajudar o leitor que deseja ampliar o estudo bÃ­blico e teolÃ³gico relacionado Ã  reflexÃ£o.</p><ul>' . $rendered . '</ul></aside>';
}

function direct_article_html(string $text, string $title): string {
    $cleaned = normalize_direct_submission_text($text);
    [$articleText, $referenceText] = split_direct_references($cleaned);
    $blocks = paragraphs_from_text($articleText);
    $body = [];
    $list = [];
    $titleSlug = slugify($title);
    $flushList = function () use (&$body, &$list): void {
        if ($list) {
            $body[] = '<ul>' . implode('', array_map(fn($item) => '<li>' . $item . '</li>', $list)) . '</ul>';
            $list = [];
        }
    };
    foreach ($blocks as $block) {
        $clean = trim((string) preg_replace('/\s*\n\s*/', ' ', $block));
        if ($clean === '') {
            continue;
        }
        if (str_starts_with($clean, '- ')) {
            $list[] = inline_direct_markup(substr($clean, 2));
            continue;
        }
        $flushList();
        $heading = trim($clean, "*# \t\n\r\0\x0B");
        if (slugify($heading) === $titleSlug) {
            continue;
        }
        if (preg_match('/^\*?\d+\.\s+.+?\*?$/u', $clean) || str_starts_with($clean, '#') || (str_starts_with($clean, '*') && str_ends_with($clean, '*') && strlen($clean) < 140) || looks_like_direct_heading($clean)) {
            $body[] = '<h2>' . inline_direct_markup($heading) . '</h2>';
        } elseif ((str_starts_with($clean, '"') || str_starts_with($clean, 'â€œ')) && preg_match('/[\p{Lu}][\p{L}]+\s+\d+:\d+/u', $clean)) {
            $body[] = '<blockquote>' . inline_direct_markup($clean) . '</blockquote>';
        } else {
            $body[] = '<p>' . inline_direct_markup($clean) . '</p>';
        }
    }
    $flushList();
    $references = direct_references_html($referenceText);
    if ($references !== '') {
        $body[] = $references;
    }
    return implode("\n", $body);
}

function decode_mime_value(string $value): string {
    if (!function_exists('imap_mime_header_decode')) {
        return $value;
    }
    $parts = imap_mime_header_decode($value);
    $decoded = '';
    foreach ($parts as $part) {
        $decoded .= $part->text ?? '';
    }
    return $decoded !== '' ? $decoded : $value;
}

function part_filename(object $part): string {
    foreach (['dparameters', 'parameters'] as $prop) {
        foreach (($part->{$prop} ?? []) as $param) {
            $attribute = strtolower((string) ($param->attribute ?? ''));
            if (in_array($attribute, ['filename', 'name'], true)) {
                return decode_mime_value((string) ($param->value ?? ''));
            }
        }
    }
    return '';
}

function collect_image_part(object $part, string $prefix = ''): ?array {
    if (!empty($part->parts)) {
        foreach ($part->parts as $index => $child) {
            $number = $prefix === '' ? (string) ($index + 1) : $prefix . '.' . ($index + 1);
            $found = collect_image_part($child, $number);
            if ($found) {
                return $found;
            }
        }
    }
    $subtype = strtolower((string) ($part->subtype ?? ''));
    $filename = strtolower(part_filename($part));
    $isImage = ((int) ($part->type ?? -1) === 5) || in_array($subtype, ['jpeg', 'jpg', 'png', 'webp', 'gif'], true);
    if (!$isImage && !preg_match('/\.(jpe?g|png|webp|gif)$/i', $filename)) {
        return null;
    }
    $ext = match ($subtype) {
        'jpeg', 'jpg' => 'jpg',
        'png' => 'png',
        'webp' => 'webp',
        'gif' => 'gif',
        default => preg_match('/\.(jpe?g|png|webp|gif)$/i', $filename, $m) ? strtolower(str_replace('jpeg', 'jpg', $m[1])) : 'jpg',
    };
    return ['part' => $prefix !== '' ? $prefix : '1', 'encoding' => (int) ($part->encoding ?? 0), 'ext' => $ext];
}

function extract_first_image_attachment($imap, int $msgNo, string $slug, string $draftId): string {
    $structure = imap_fetchstructure($imap, $msgNo);
    if (!$structure) {
        return '';
    }
    $found = collect_image_part($structure);
    if (!$found) {
        return '';
    }
    if (!is_dir(IMAGE_DIR)) {
        mkdir(IMAGE_DIR, 0755, true);
    }
    $payload = imap_fetchbody($imap, $msgNo, (string) $found['part']);
    if ((int) $found['encoding'] === 3) {
        $payload = base64_decode($payload) ?: '';
    } elseif ((int) $found['encoding'] === 4) {
        $payload = quoted_printable_decode($payload);
    }
    if (!is_string($payload) || strlen($payload) < 100) {
        return '';
    }
    $filename = $slug . '-' . $draftId . '.' . $found['ext'];
    file_put_contents(IMAGE_DIR . '/' . $filename, $payload);
    return $filename;
}

function listen_controls(): string {
    return '<div class="listen-tools" aria-label="NarraÃ§Ã£o do artigo"><button class="listen-button" type="button" data-listen-toggle aria-label="Ouvir artigo" title="Ouvir artigo"><svg aria-hidden="true" viewBox="0 0 24 24" width="22" height="22"><path d="M4 9v6h4l5 4V5L8 9H4z" fill="currentColor"></path><path d="M16 9.5c1.1 1.4 1.1 3.6 0 5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path><path d="M18.8 7c2.3 2.8 2.3 7.2 0 10" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path></svg></button><span data-listen-status>Clique para ouvir o artigo.</span></div>';
}

function top_book_strip(): string {
    return '<section class="top-book-strip" aria-label="Livro em destaque"><span>Livro gratuito do autor</span><strong>Servir atravÃ©s da IntercessÃ£o</strong><a href="https://www.editorakaleo.com/product-page/servir-atrav%C3%A9s-da-intercess%C3%A3o" target="_blank" rel="noopener">Acessar e-book</a></section>';
}

function related_articles_html(string $currentSlug): string {
    $items = [
        ['slug' => 'luta-invisivel', 'title' => 'Luta InvisÃ­vel', 'excerpt' => 'A intercessÃ£o como serviÃ§o silencioso, amor pastoral e perseveranÃ§a diante de Deus.'],
        ['slug' => 'tesouros-escondidos-em-cristo-a-sabedoria-que-transforma', 'title' => 'Tesouros escondidos em Cristo', 'excerpt' => 'A sabedoria que transforma nasce do conhecimento profundo de Cristo.'],
        ['slug' => 'palavras-que-enganam-vigilancia-e-discernimento-na-vida-crista', 'title' => 'Palavras que Enganam', 'excerpt' => 'Discernimento espiritual para reconhecer discursos sedutores e permanecer firme na verdade.'],
        ['slug' => 'o-coracao-desordenado-guardando-a-fonte-da-vida', 'title' => 'O CoraÃ§Ã£o Desordenado', 'excerpt' => 'Uma reflexÃ£o sobre guardar a fonte da vida e ordenar o coraÃ§Ã£o diante de Deus.'],
    ];
    $cards = '';
    $count = 0;
    foreach ($items as $item) {
        if ($item['slug'] === $currentSlug) {
            continue;
        }
        $cards .= '<a class="related-card" href="../artigos/' . esc($item['slug']) . '.html"><strong>' . esc($item['title']) . '</strong><span>' . esc($item['excerpt']) . '</span></a>';
        $count++;
        if ($count >= 3) {
            break;
        }
    }
    return '<aside class="related-reading" aria-label="Leia tambem"><p>Leia tambÃ©m</p><h2>Continue a reflexÃ£o</h2><div class="related-grid">' . $cards . '</div></aside>';
}

function listen_script(): string {
    return '<script>(()=>{const c=document.querySelector(".listen-tools"),a=document.querySelector(".article-content");if(!c||!a||!("speechSynthesis" in window))return;const s=c.querySelector("[data-listen-status]"),b=c.querySelector("[data-listen-toggle]"),y=window.speechSynthesis;let u=null;const m=t=>{if(s)s.textContent=t},k=v=>{if(!b)return;b.classList.toggle("is-speaking",v);b.setAttribute("aria-label",v?"Pausar narraÃ§Ã£o":"Ouvir artigo");b.setAttribute("title",v?"Pausar narraÃ§Ã£o":"Ouvir artigo")},x=t=>t.replace(/\b([1-3]?\s?[A-ZÃ€-Ã–Ã˜-Ãž][A-Za-zÃ€-Ã¿]+)\s+(\d{1,3}):(\d{1,3})(?:-(\d{1,3}))?/g,(_,l,p,v,f)=>f?`${l}, capÃ­tulo ${p}, versÃ­culos ${v} a ${f}`:`${l}, capÃ­tulo ${p}, versÃ­culo ${v}`);c.addEventListener("click",e=>{if(!e.target.closest("[data-listen-toggle]"))return;if(y.speaking&&!y.paused){y.pause();k(false);m("NarraÃ§Ã£o pausada.");return}if(y.paused){y.resume();k(true);m("Narrando artigo.");return}y.cancel();u=new SpeechSynthesisUtterance(x(a.innerText).replace(/\s+/g," ").trim());u.lang="pt-BR";u.rate=.95;u.onend=()=>{k(false);m("NarraÃ§Ã£o concluÃ­da.")};u.onerror=()=>{k(false);m("NÃ£o foi possÃ­vel narrar este artigo.")};y.speak(u);k(true);m("Narrando artigo.")});window.addEventListener("beforeunload",()=>y.cancel())})();</script>';
}

function render_article_page(array $draft): string {
    $title = (string) ($draft['title'] ?? 'Nova reflexÃ£o');
    $excerpt = (string) ($draft['excerpt'] ?? 'Uma reflexÃ£o cristÃ£ para fortalecer a fÃ© na vida cotidiana.');
    $category = (string) ($draft['category'] ?? 'ReflexÃ£o');
    $author = (string) ($draft['author'] ?? DEFAULT_AUTHOR);
    $slug = (string) ($draft['slug'] ?? slugify($title));
    $image = (string) ($draft['image_filename'] ?? '');
    $imageHtml = $image !== '' ? '<img src="../images/articles/' . esc($image) . '" alt="' . esc($title) . '" />' : '';
    $seoTitle = trim((string) ($draft['seo_title'] ?? '')) ?: $title;
    if (stripos($seoTitle, 'verbo vivo') === false) {
        $seoTitle .= ' | Verbo Vivo';
    }
    $seoDescription = trim((string) ($draft['seo_description'] ?? '')) ?: $excerpt;
    $articleUrl = DOMAIN . '/artigos/' . $slug . '.html';
    $imageUrl = $image !== '' ? DOMAIN . '/images/articles/' . $image : '';
    $schema = ['@context' => 'https://schema.org', '@type' => 'BlogPosting', 'mainEntityOfPage' => ['@type' => 'WebPage', '@id' => $articleUrl], 'headline' => $title, 'description' => $seoDescription, 'image' => $imageUrl !== '' ? [$imageUrl] : [], 'author' => ['@type' => 'Person', 'name' => $author, 'url' => DOMAIN . '/autor.html'], 'publisher' => ['@type' => 'Organization', 'name' => 'Verbo Vivo', 'url' => DOMAIN], 'inLanguage' => 'pt-BR', 'articleSection' => $category];
    if (!empty($draft['seo_keywords'])) {
        $schema['keywords'] = (string) $draft['seo_keywords'];
    }
    $schemaJson = json_encode($schema, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT);
    return '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>' . esc($seoTitle) . '</title><meta name="description" content="' . esc($seoDescription) . '" /><link rel="canonical" href="' . esc($articleUrl) . '" /><meta property="og:type" content="article" /><meta property="og:title" content="' . esc($title) . '" /><meta property="og:description" content="' . esc($seoDescription) . '" /><meta property="og:url" content="' . esc($articleUrl) . '" />' . ($imageUrl !== '' ? '<meta property="og:image" content="' . esc($imageUrl) . '" />' : '') . '<meta name="twitter:card" content="summary_large_image" /><script type="application/ld+json">' . $schemaJson . '</script><link rel="stylesheet" href="../styles.css?v=20260604-book-strip" /></head><body><header class="site-header"><a class="brand" href="../index.html"><span class="brand-mark">VV</span><span><strong>Verbo Vivo</strong><small>verbovivo.blog</small></span></a><nav aria-label="NavegaÃ§Ã£o principal"><a href="../index.html#artigos">Artigos</a><a href="../autor.html">Autor</a><a href="../sobre.html">Sobre</a><a href="../contato.html">Contato</a><a href="../faq.html">FAQ</a></nav></header>' . top_book_strip() . '<main><article class="article-page"><header class="article-hero"><div><p class="category">' . esc($category) . '</p><h1>' . esc($title) . '</h1><p class="article-excerpt">' . esc($excerpt) . '</p><p class="article-meta">Por ' . esc($author) . '</p>' . author_socials_html($draft['author_socials'] ?? []) . listen_controls() . '</div>' . $imageHtml . '</header><div class="article-content">' . (string) ($draft['body_html'] ?? '') . '</div>' . related_articles_html($slug) . '</article></main><footer class="site-footer"><p><strong>Verbo Vivo</strong> publica reflexÃµes cristÃ£s para fortalecer a fÃ© na vida cotidiana.</p><div><a href="../autor.html">Autor</a><a href="../sobre.html">Sobre</a><a href="../contato.html">Contato</a><a href="../faq.html">FAQ</a><a href="https://instagram.com/tec.agora" target="_blank" rel="noopener">By @tec.agora</a></div></footer>' . listen_script() . '</body></html>';
}

function article_card(array $draft): string {
    $image = (string) ($draft['image_filename'] ?? 'o-coracao-desordenado-guardando-a-fonte-da-vida-dcf1e0e616343e53.png');
    return '<article class="article-card"><a href="artigos/' . esc((string) $draft['slug']) . '.html"><img src="images/articles/' . esc($image) . '" alt="' . esc((string) $draft['title']) . '" /></a><div class="article-body"><p class="category">' . esc((string) $draft['category']) . '</p><h3><a href="artigos/' . esc((string) $draft['slug']) . '.html">' . esc((string) $draft['title']) . '</a></h3><p>' . esc((string) $draft['excerpt']) . '</p></div></article>';
}

function featured_article(array $draft): string {
    $image = (string) ($draft['image_filename'] ?? 'o-coracao-desordenado-guardando-a-fonte-da-vida-dcf1e0e616343e53.png');
    return '<article class="featured"><a href="artigos/' . esc((string) $draft['slug']) . '.html"><img src="images/articles/' . esc($image) . '" alt="' . esc((string) $draft['title']) . '" /></a><div class="article-body"><p class="category">' . esc((string) $draft['category']) . '</p><h3><a href="artigos/' . esc((string) $draft['slug']) . '.html">' . esc((string) $draft['title']) . '</a></h3><p>' . esc((string) $draft['excerpt']) . '</p></div></article>';
}

function update_index(array $draft): void {
    $path = __DIR__ . '/index.html';
    $html = (string) file_get_contents($path);
    $needle = 'artigos/' . (string) $draft['slug'] . '.html';
    $wasListed = str_contains($html, $needle);
    $html = (string) preg_replace('/\s*<article class="featured">.*?<\/article>/s', "\n" . featured_article($draft), $html, 1);
    if (!$wasListed) {
        $html = (string) preg_replace('/(<section\b[^>]*class="[^"]*\barticle-grid\b[^"]*"[^>]*>)/', '$1' . "\n        " . article_card($draft), $html, 1);
    }
    file_put_contents($path, $html);
}

function update_feed(array $draft): void {
    $path = __DIR__ . '/feed.xml';
    $xml = (string) file_get_contents($path);
    $url = DOMAIN . '/artigos/' . (string) $draft['slug'] . '.html';
    if (str_contains($xml, $url)) {
        return;
    }
    $description = trim((string) ($draft['seo_description'] ?? '')) ?: (string) $draft['excerpt'];
    $item = '<item><title>' . esc((string) $draft['title']) . '</title><link>' . $url . '</link><guid>' . $url . '</guid><description>' . esc($description) . '</description><pubDate>' . gmdate(DATE_RSS) . '</pubDate></item>';
    $xml = str_replace('    <item>', '    ' . $item . "\n    <item>", $xml);
    file_put_contents($path, $xml);
}

function update_sitemap(array $draft): void {
    $path = __DIR__ . '/sitemap.xml';
    $xml = (string) file_get_contents($path);
    $url = DOMAIN . '/artigos/' . (string) $draft['slug'] . '.html';
    if (str_contains($xml, $url)) {
        return;
    }
    $entry = '  <url><loc>' . $url . '</loc><lastmod>' . gmdate('Y-m-d') . '</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>' . "\n";
    $xml = str_replace('</urlset>', $entry . '</urlset>', $xml);
    file_put_contents($path, $xml);
}

function publish_draft(array $draft): void {
    if (!is_dir(ARTICLE_DIR)) {
        mkdir(ARTICLE_DIR, 0755, true);
    }
    file_put_contents(ARTICLE_DIR . '/' . (string) $draft['slug'] . '.html', render_article_page($draft));
    update_index($draft);
    update_feed($draft);
    update_sitemap($draft);
}

function direct_article_from_email(string $subject, string $source, string $sender, string $imageFilename): array {
    [$metadata, $articleText] = extract_submission_metadata($source);
    $articleText = normalize_direct_submission_text($articleText);
    $title = trim($subject) !== '' ? trim($subject) : 'Nova reflexÃ£o';
    $slug = slugify($title);
    $excerpt = trim_sentence($articleText, 154) ?: 'Uma reflexÃ£o cristÃ£ para fortalecer a fÃ© na vida cotidiana.';
    return [
        'id' => bin2hex(random_bytes(8)),
        'token' => rtrim(strtr(base64_encode(random_bytes(24)), '+/', '-_'), '='),
        'sender' => $sender,
        'source_subject' => $subject,
        'source_text' => $articleText,
        'title' => $title,
        'slug' => $slug,
        'excerpt' => $excerpt,
        'category' => 'ReflexÃ£o',
        'author' => submission_author($metadata),
        'author_socials' => submission_socials($metadata),
        'body_html' => direct_article_html($articleText, $title),
        'image_prompt' => '',
        'image_filename' => $imageFilename,
        'seo_title' => trim_sentence($title, 58),
        'seo_description' => $excerpt,
        'seo_keywords' => implode(' ', array_slice(array_filter(explode('-', $slug), fn($word) => strlen($word) > 2), 0, 6)),
        'status' => 'published_direct',
        'created_at' => gmdate(DATE_ATOM),
        'published_at' => gmdate(DATE_ATOM),
    ];
}

function refine_article(array $config, string $source, string $subject, string $sender): array {
    [$metadata, $articleText] = extract_submission_metadata($source);
    $response = openai_json($config, [
        'model' => 'gpt-4.1-mini',
        'messages' => [
            ['role' => 'system', 'content' => 'VocÃª Ã© o editor cristÃ£o do blog Verbo Vivo. Transforme textos brutos humanos em reflexÃ£o curta, acolhedora, inteligÃ­vel e biblicamente coerente. NÃ£o mencione IA ou automaÃ§Ã£o. Escreva em portuguÃªs do Brasil. Escreva referÃªncias bÃ­blicas por extenso, como Mateus, capÃ­tulo 21, versÃ­culo 17, nunca no formato 21:17. Mantenha title como tÃ­tulo editorial do artigo. Crie seo_title com atÃ© 60 caracteres, mais pesquisÃ¡vel no Google, sem sensacionalismo. Crie excerpt e seo_description com atÃ© 155 caracteres, fiÃ©is ao texto e Ãºteis para busca. Crie seo_keywords com uma expressÃ£o principal de busca.'],
            ['role' => 'user', 'content' => "Responda somente JSON vÃ¡lido com as chaves title, seo_title, category, excerpt, seo_description, seo_keywords, quote, sections, image_prompt. sections deve ser lista de objetos com heading e paragraphs.\n\nAssunto: $subject\n\nTexto:\n$articleText"],
        ],
        'response_format' => ['type' => 'json_object'],
        'temperature' => 0.7,
    ]);
    $content = $response['choices'][0]['message']['content'] ?? '{}';
    $data = json_decode((string) $content, true) ?: [];
    $title = (string) ($data['title'] ?? $subject ?: 'Nova reflexÃ£o');
    $slug = slugify($title);
    $body = '';
    if (!empty($data['quote'])) {
        $body .= '<blockquote>' . esc((string) $data['quote']) . '</blockquote>';
    }
    foreach (($data['sections'] ?? []) as $section) {
        $heading = trim((string) ($section['heading'] ?? ''));
        if ($heading !== '') {
            $body .= '<h2>' . esc($heading) . '</h2>';
        }
        foreach (($section['paragraphs'] ?? []) as $paragraph) {
            $body .= '<p>' . esc((string) $paragraph) . '</p>';
        }
    }
    $draftId = bin2hex(random_bytes(8));
    return [
        'id' => $draftId,
        'token' => rtrim(strtr(base64_encode(random_bytes(24)), '+/', '-_'), '='),
        'sender' => $sender,
        'source_subject' => $subject,
        'source_text' => $articleText,
        'title' => $title,
        'slug' => $slug,
        'excerpt' => (string) ($data['excerpt'] ?? 'Uma reflexÃ£o cristÃ£ para fortalecer a fÃ© na vida cotidiana.'),
        'category' => (string) ($data['category'] ?? 'ReflexÃ£o'),
        'author' => submission_author($metadata),
        'author_socials' => submission_socials($metadata),
        'body_html' => $body,
        'image_prompt' => (string) ($data['image_prompt'] ?? $title),
        'image_filename' => $slug . '-' . $draftId . '.png',
        'seo_title' => (string) ($data['seo_title'] ?? ''),
        'seo_description' => (string) ($data['seo_description'] ?? ($data['excerpt'] ?? '')),
        'seo_keywords' => (string) ($data['seo_keywords'] ?? ''),
        'status' => 'pending_review',
        'created_at' => gmdate(DATE_ATOM),
    ];
}

function process_editorial(array $config): int {
    if (!function_exists('imap_open')) {
        throw new RuntimeException('PHP IMAP extension is unavailable.');
    }
    $mailbox = sprintf('{%s:%d/imap/ssl}INBOX', $config['editorial_imap_host'], $config['editorial_imap_port']);
    $imap = imap_open($mailbox, $config['editorial_imap_user'], $config['editorial_imap_password']);
    if (!$imap) {
        throw new RuntimeException('Could not open editorial inbox: ' . imap_last_error());
    }
    $ids = imap_search($imap, 'UNSEEN') ?: [];
    $processed = 0;
    foreach ($ids as $msgNo) {
        $header = imap_headerinfo($imap, (int) $msgNo);
        $from = $header->from[0]->mailbox . '@' . $header->from[0]->host;
        if (str_ends_with($from, '@email.hostinger.com')) {
            imap_setflag_full($imap, (string) $msgNo, '\\Seen');
            continue;
        }
        $subject = isset($header->subject) ? imap_utf8((string) $header->subject) : 'Nova reflexÃ£o';
        $messageId = (string) ($header->message_id ?? ('msg-' . $msgNo));
        if (!is_sender_authorized($config, 'artigo@verbovivo.blog', $from, $subject, $messageId)) {
            request_sender_authorization($config, 'artigo@verbovivo.blog', $from, $subject, $messageId);
            continue;
        }
        $text = extract_body($imap, (int) $msgNo);
        if ($text === '') {
            continue;
        }
        $draft = refine_article($config, $text, $subject, $from);
        if (!is_dir(IMAGE_DIR)) {
            mkdir(IMAGE_DIR, 0755, true);
        }
        openai_image($config, (string) $draft['image_prompt'], IMAGE_DIR . '/' . $draft['image_filename']);
        save_review_draft_file($draft);
        smtp_send($config, $from, 'Artigo pronto para aprovaÃ§Ã£o: ' . $draft['title'], email_preview($draft), 'Artigo pronto para revisÃ£o: ' . DOMAIN . '/revisao.php?token=' . $draft['token']);
        imap_setflag_full($imap, (string) $msgNo, '\\Seen');
        $processed++;
    }
    imap_close($imap);
    return $processed;
}

function process_publish(array $config): int {
    if (!function_exists('imap_open')) {
        throw new RuntimeException('PHP IMAP extension is unavailable.');
    }
    foreach (['publish_imap_host', 'publish_imap_port', 'publish_imap_user', 'publish_imap_password'] as $key) {
        if (trim((string) ($config[$key] ?? '')) === '') {
            throw new RuntimeException('Missing direct publish config: ' . $key);
        }
    }
    $mailbox = sprintf('{%s:%d/imap/ssl}INBOX', $config['publish_imap_host'], $config['publish_imap_port']);
    $imap = imap_open($mailbox, $config['publish_imap_user'], $config['publish_imap_password']);
    if (!$imap) {
        throw new RuntimeException('Could not open direct publish inbox: ' . imap_last_error());
    }
    $ids = imap_search($imap, 'UNSEEN') ?: [];
    $processed = 0;
    foreach ($ids as $msgNo) {
        $header = imap_headerinfo($imap, (int) $msgNo);
        $from = $header->from[0]->mailbox . '@' . $header->from[0]->host;
        if (str_ends_with($from, '@email.hostinger.com')) {
            imap_setflag_full($imap, (string) $msgNo, '\\Seen');
            continue;
        }
        $subject = isset($header->subject) ? imap_utf8((string) $header->subject) : 'Nova reflexÃ£o';
        $messageId = (string) ($header->message_id ?? ('msg-' . $msgNo));
        if (!is_sender_authorized($config, 'publicar@verbovivo.blog', $from, $subject, $messageId)) {
            request_sender_authorization($config, 'publicar@verbovivo.blog', $from, $subject, $messageId);
            continue;
        }
        $text = extract_body($imap, (int) $msgNo);
        if ($text === '') {
            vv_log('Direct publish skipped empty message: ' . $subject);
            continue;
        }
        $draftId = bin2hex(random_bytes(8));
        $slug = slugify($subject);
        $imageFilename = extract_first_image_attachment($imap, (int) $msgNo, $slug, $draftId);
        if ($imageFilename === '') {
            vv_log('Direct publish skipped missing image attachment: ' . $subject);
            continue;
        }
        $draft = direct_article_from_email($subject, $text, $from, $imageFilename);
        $draft['id'] = $draftId;
        save_review_draft_file($draft);
        publish_draft($draft);
        imap_setflag_full($imap, (string) $msgNo, '\\Seen');
        vv_log('Direct publish completed: ' . $draft['slug']);
        $processed++;
    }
    imap_close($imap);
    return $processed;
}

try {
    vv_log('Cron started.');
    $editorialCount = process_editorial($config);
    vv_log("Editorial processed: $editorialCount");
    $publishCount = process_publish($config);
    vv_log("Direct publish processed: $publishCount");
} catch (Throwable $e) {
    vv_log('ERROR: ' . $e->getMessage());
    exit(1);
}
