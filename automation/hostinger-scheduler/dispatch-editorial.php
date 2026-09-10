<?php
declare(strict_types=1);

// Staged only. Install outside public_html after credentials and cron are verified.
if (PHP_SAPI !== 'cli') {
    http_response_code(404);
    exit;
}

function github_request(string $token, string $path, ?array $payload = null): array {
    $curl = curl_init('https://api.github.com/repos/HeberPython/verbovivo.blog/' . $path);
    curl_setopt_array($curl, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_FOLLOWLOCATION => false,
        CURLOPT_HTTPHEADER => [
            'Accept: application/vnd.github+json',
            'Authorization: Bearer ' . $token,
            'X-GitHub-Api-Version: 2022-11-28',
            'User-Agent: VerboVivo-Hostinger-Scheduler',
        ],
    ]);
    if ($payload !== null) {
        curl_setopt($curl, CURLOPT_POST, true);
        curl_setopt($curl, CURLOPT_POSTFIELDS, json_encode($payload, JSON_THROW_ON_ERROR));
    }
    $body = curl_exec($curl);
    $status = curl_getinfo($curl, CURLINFO_RESPONSE_CODE);
    curl_close($curl);
    if ($body === false || $status < 200 || $status >= 300) {
        // Never log authorization headers, API response bodies or credentials.
        throw new RuntimeException('GitHub request failed; HTTP ' . $status);
    }
    return $body === '' ? [] : json_decode($body, true, 512, JSON_THROW_ON_ERROR);
}

try {
    if (!extension_loaded('curl')) {
        throw new RuntimeException('PHP cURL is required.');
    }
    $configPath = __DIR__ . '/scheduler-config.json';
    if (!is_file($configPath)) {
        throw new RuntimeException('Private scheduler configuration is missing.');
    }
    $config = json_decode((string) file_get_contents($configPath), true, 512, JSON_THROW_ON_ERROR);
    $token = trim((string) ($config['github_token'] ?? ''));
    if ($token === '') {
        throw new RuntimeException('Dedicated GitHub token is missing.');
    }
    $check = in_array('--check', $argv, true);
    $command = (string) ($config['command'] ?? 'email-audit');
    if (!in_array($command, ['email-audit', 'all'], true)) {
        throw new RuntimeException('Invalid scheduler command.');
    }
    if (!$check && ($config['enabled'] ?? false) !== true) {
        throw new RuntimeException('Scheduler is not activated.');
    }
    $now = new DateTimeImmutable('now', new DateTimeZone('America/Sao_Paulo'));
    $hour = (int) $now->format('G');
    if (!$check && ($hour < 7 || $hour >= 23)) {
        echo $now->format(DATE_ATOM) . " outside operating hours\n";
        exit(0);
    }
    $lock = fopen(__DIR__ . '/scheduler.lock', 'c+');
    if (!$lock || !flock($lock, LOCK_EX | LOCK_NB)) {
        throw new RuntimeException('Another scheduler instance is active.');
    }
    $workflow = 'actions/workflows/editorial-agent.yml';
    $details = github_request($token, $workflow);
    if (($details['state'] ?? '') !== 'active') {
        throw new RuntimeException('Editorial workflow is not active.');
    }
    if ($check) {
        echo "GitHub read access verified. No workflow dispatched; write permission not yet tested.\n";
        exit(0);
    }
    foreach (['queued', 'in_progress', 'pending', 'waiting', 'requested'] as $status) {
        $runs = github_request($token, $workflow . '/runs?branch=main&per_page=1&status=' . $status);
        if (!isset($runs['workflow_runs']) || !is_array($runs['workflow_runs'])) {
            throw new RuntimeException('Invalid workflow status response.');
        }
        if ($runs['workflow_runs']) {
            echo $now->format(DATE_ATOM) . " workflow already active; no duplicate dispatch\n";
            exit(0);
        }
    }
    $lastAttempt = (int) trim((string) stream_get_contents($lock));
    $slot = intdiv(time(), 900);
    if ($lastAttempt === $slot) {
        echo $now->format(DATE_ATOM) . " dispatch cooldown\n";
        exit(0);
    }
    // Record before POST: an ambiguous timeout must not cause an immediate duplicate.
    rewind($lock);
    ftruncate($lock, 0);
    fwrite($lock, (string) $slot);
    fflush($lock);
    github_request($token, $workflow . '/dispatches', [
        'ref' => 'main', 'inputs' => ['command' => $command],
    ]);
    echo $now->format(DATE_ATOM) . " dispatch accepted; execution completion must be checked in GitHub\n";
} catch (Throwable $error) {
    fwrite(STDERR, 'Scheduler error: ' . $error->getMessage() . "\n");
    exit(1);
}
