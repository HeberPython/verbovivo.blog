<?php
declare(strict_types=1);

const DOMAIN = 'https://verbovivo.blog';
const DRAFT_DIR = __DIR__ . '/_editorial_drafts';
const ARTICLE_DIR = __DIR__ . '/artigos';
const IMAGE_DIR = __DIR__ . '/images/articles';
const CONFIG_FILE = __DIR__ . '/_private/editorial-config.php';

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
    echo '[' . gmdate('c') . '] ' . $message . PHP_EOL;
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
    return [
        'instagram' => '◎',
        'facebook' => 'f',
        'youtube' => '▶',
        'x' => 'X',
        'twitter' => 'X',
        'linkedin' => 'in',
        'site' => '↗',
        'website' => '↗',
    ][$name] ?? '↗';
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
        $links[] = '<a href="' . esc($href) . '" target="_blank" rel="noopener"><span aria-hidden="true">' . esc(social_icon((string) $name)) . '</span> ' . esc(social_label((string) $name)) . ' ' . esc($display) . '</a>';
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
    $count = process_editorial($config);
    vv_log("Editorial processed: $count");
} catch (Throwable $e) {
    vv_log('ERROR: ' . $e->getMessage());
    exit(1);
}
