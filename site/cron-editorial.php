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

if (php_sapi_name() !== 'cli') {
    http_response_code(403);
    exit('Forbidden');
}

if (!is_file(CONFIG_FILE)) {
    fwrite(STDERR, "Missing private config.\n");
    exit(1);
}

$config = require CONFIG_FILE;

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
    $metadata = ['author' => '', 'socials' => []];
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
            if (in_array($key, ['autor', 'author', 'nome', 'nome do autor'], true)) {
                $metadata['author'] = $value;
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
        $display = (string) $url;
        if (str_starts_with($href, '@')) {
            $handle = ltrim($href, '@');
            if ($name === 'instagram') {
                $href = 'https://instagram.com/' . $handle;
            } elseif ($name === 'x' || $name === 'twitter') {
                $href = 'https://x.com/' . $handle;
            }
        }
        $label = trim(social_label((string) $name) . ' ' . $display);
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
        'prompt' => 'Crie uma imagem editorial cristã, reverente, sem texto escrito na imagem, sem retratar Jesus de forma literal, com atmosfera contemplativa: ' . $prompt,
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

function smtp_send(array $config, string $to, string $subject, string $html, string $text): void {
    $boundary = 'vv_' . bin2hex(random_bytes(12));
    $headers = [
        'From: Verbo Vivo <' . $config['editorial_smtp_user'] . '>',
        'MIME-Version: 1.0',
        'Content-Type: multipart/alternative; boundary="' . $boundary . '"',
    ];
    $body = "--$boundary\r\nContent-Type: text/plain; charset=UTF-8\r\n\r\n$text\r\n";
    $body .= "--$boundary\r\nContent-Type: text/html; charset=UTF-8\r\n\r\n$html\r\n--$boundary--\r\n";
    if (!mail($to, '=?UTF-8?B?' . base64_encode($subject) . '?=', $body, implode("\r\n", $headers))) {
        throw new RuntimeException('PHP mail() failed.');
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

function refine_article(array $config, string $source, string $subject, string $sender): array {
    [$metadata, $articleText] = extract_submission_metadata($source);
    $response = openai_json($config, [
        'model' => 'gpt-4.1-mini',
        'messages' => [
            ['role' => 'system', 'content' => 'Você é o editor cristão do blog Verbo Vivo. Transforme textos brutos humanos em reflexão curta, acolhedora, inteligível e biblicamente coerente. Não mencione IA ou automação. Escreva em português do Brasil. Escreva referências bíblicas por extenso, como Mateus, capítulo 21, versículo 17, nunca no formato 21:17.'],
            ['role' => 'user', 'content' => "Responda somente JSON válido com as chaves title, category, excerpt, quote, sections, image_prompt. sections deve ser lista de objetos com heading e paragraphs.\n\nAssunto: $subject\n\nTexto:\n$articleText"],
        ],
        'response_format' => ['type' => 'json_object'],
        'temperature' => 0.7,
    ]);
    $content = $response['choices'][0]['message']['content'] ?? '{}';
    $data = json_decode((string) $content, true) ?: [];
    $title = (string) ($data['title'] ?? $subject ?: 'Nova reflexão');
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
    return [
        'id' => bin2hex(random_bytes(8)),
        'token' => rtrim(strtr(base64_encode(random_bytes(24)), '+/', '-_'), '='),
        'sender' => $sender,
        'source_subject' => $subject,
        'source_text' => $articleText,
        'title' => $title,
        'slug' => $slug,
        'excerpt' => (string) ($data['excerpt'] ?? 'Uma reflexão cristã para fortalecer a fé na vida cotidiana.'),
        'category' => (string) ($data['category'] ?? 'Reflexão'),
        'author' => $metadata['author'] ?: 'Autor informado na publicação',
        'author_socials' => $metadata['socials'],
        'body_html' => $body,
        'image_prompt' => (string) ($data['image_prompt'] ?? $title),
        'image_filename' => $slug . '.png',
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
        $subject = isset($header->subject) ? imap_utf8((string) $header->subject) : 'Nova reflexão';
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
        if (!is_dir(DRAFT_DIR)) {
            mkdir(DRAFT_DIR, 0755, true);
        }
        file_put_contents(DRAFT_DIR . '/' . $draft['token'] . '.json', json_encode($draft, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
        smtp_send($config, $from, 'Artigo pronto para aprovação: ' . $draft['title'], email_preview($draft), 'Artigo pronto para revisão: ' . DOMAIN . '/revisao.php?token=' . $draft['token']);
        imap_setflag_full($imap, (string) $msgNo, '\\Seen');
        $processed++;
    }
    imap_close($imap);
    return $processed;
}

try {
    vv_log('Cron started.');
    $count = process_editorial($config);
    vv_log("Editorial processed: $count");
} catch (Throwable $e) {
    vv_log('ERROR: ' . $e->getMessage());
    exit(1);
}
