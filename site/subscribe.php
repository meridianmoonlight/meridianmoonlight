<?php
/**
 * Meridian Moonlight — signup handler (SMTP version)
 *
 * Sends notifications through Namecheap Private Email's SMTP server, authenticated
 * as your own mailbox. Mail then leaves from the server your SPF and DKIM records
 * actually authorize, so it passes authentication instead of being dropped.
 *
 * This file goes in public_html, beside index.html.
 * Credentials live in moonlight-config.php, ONE LEVEL ABOVE public_html.
 */

declare(strict_types=1);

const STORE_FILE   = __DIR__ . '/../moonlight-pledges.csv';
const CONFIG_FILE  = __DIR__ . '/../moonlight-config.php';
const ERROR_LOG    = __DIR__ . '/../moonlight-errors.log';
const MAX_PER_HOUR = 12;
const OK_MESSAGE   = 'Pledged. You\'ll hear once, when the first node is ready to test.';

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');

function out(bool $ok, string $message, int $code = 200): never {
    http_response_code($code);
    echo json_encode(['ok' => $ok, 'message' => $message]);
    exit;
}

function logError(string $msg): void {
    @file_put_contents(ERROR_LOG, date('c') . ' ' . $msg . "\n", FILE_APPEND | LOCK_EX);
}

/* ------------------------------------------------------------------ guards */

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    out(false, 'Method not allowed.', 405);
}

// Honeypot — invisible to people, irresistible to bots.
// Report success so the bot doesn't retry.
if (trim((string)($_POST['website'] ?? '')) !== '') {
    out(true, OK_MESSAGE);
}

$email = trim((string)($_POST['email'] ?? ''));

if ($email === ''
    || strlen($email) > 254
    || !filter_var($email, FILTER_VALIDATE_EMAIL)
    || preg_match('/[\r\n]/', $email)) {
    out(false, 'That email address doesn\'t look right.');
}

$ip = (string)($_SERVER['REMOTE_ADDR'] ?? 'unknown');

/* -------------------------------------------------------------- rate limit */

$bucket = sys_get_temp_dir() . '/mm_rate_' . md5($ip) . '.txt';
$hits   = [];
if (is_readable($bucket)) {
    $hits = array_filter(array_map('intval', explode(',', (string)file_get_contents($bucket))));
}
$cutoff = time() - 3600;
$hits   = array_values(array_filter($hits, static fn(int $t): bool => $t > $cutoff));

if (count($hits) >= MAX_PER_HOUR) {
    out(false, 'Too many attempts. Try again later, or email hello@meridianmoonlight.com.', 429);
}
$hits[] = time();
@file_put_contents($bucket, implode(',', $hits), LOCK_EX);

/* ------------------------------------------------------------------- store */
/* Storage runs first and matters most. Even if the notification fails,
   the pledge is never lost.                                                  */

$stored = false;
$fh = @fopen(STORE_FILE, 'a');
if ($fh !== false) {
    if (flock($fh, LOCK_EX)) {
        if (ftell($fh) === 0) {
            fputcsv($fh, ['timestamp', 'email', 'ip']);
        }
        fputcsv($fh, [date('c'), $email, $ip]);
        fflush($fh);
        flock($fh, LOCK_UN);
        $stored = true;
    }
    fclose($fh);
    @chmod(STORE_FILE, 0600);
} else {
    logError('Could not open store file for: ' . $email);
}

/* ------------------------------------------------------------- smtp client */

/**
 * Minimal SMTP client — no dependencies, since shared hosting rarely has Composer.
 * @throws RuntimeException
 */
function smtpSend(array $cfg, string $subject, string $body): void {
    $port      = (int)$cfg['port'];
    $transport = ($port === 465 ? 'ssl://' : 'tcp://') . $cfg['host'] . ':' . $port;

    $ctx = stream_context_create([
        'ssl' => ['verify_peer' => true, 'verify_peer_name' => true],
    ]);

    $fp = @stream_socket_client($transport, $errno, $errstr, 15, STREAM_CLIENT_CONNECT, $ctx);
    if (!$fp) {
        throw new RuntimeException("connect failed: {$errstr} ({$errno})");
    }
    stream_set_timeout($fp, 15);

    $read = static function () use ($fp): string {
        $data = '';
        while (($line = fgets($fp, 515)) !== false) {
            $data .= $line;
            // The final line of a reply has a space in position 4, not a hyphen.
            if (strlen($line) < 4 || $line[3] !== '-') {
                break;
            }
        }
        return $data;
    };

    $cmd = static function (string $c, string $expect) use ($fp, $read): string {
        if ($c !== '') {
            fwrite($fp, $c . "\r\n");
        }
        $r = $read();
        if (strncmp($r, $expect, strlen($expect)) !== 0) {
            $label = $c === '' ? 'greeting' : explode(' ', $c)[0];
            throw new RuntimeException('unexpected reply to ' . $label . ': ' . trim($r));
        }
        return $r;
    };

    $helo = $cfg['helo'] ?? 'localhost';

    $cmd('', '220');
    $cmd('EHLO ' . $helo, '250');

    // STARTTLS path, used when port is 587.
    if ($port === 587) {
        $cmd('STARTTLS', '220');
        if (!stream_socket_enable_crypto($fp, true, STREAM_CRYPTO_METHOD_TLS_CLIENT)) {
            throw new RuntimeException('STARTTLS negotiation failed');
        }
        $cmd('EHLO ' . $helo, '250');
    }

    $cmd('AUTH LOGIN', '334');
    $cmd(base64_encode((string)$cfg['user']), '334');
    $cmd(base64_encode((string)$cfg['pass']), '235');

    $cmd('MAIL FROM:<' . $cfg['from'] . '>', '250');
    $cmd('RCPT TO:<' . $cfg['to'] . '>', '250');
    $cmd('DATA', '354');

    $headers = [
        'From: Meridian Moonlight <' . $cfg['from'] . '>',
        'To: <' . $cfg['to'] . '>',
        'Subject: ' . $subject,
        'Date: ' . date('r'),
        'MIME-Version: 1.0',
        'Content-Type: text/plain; charset=utf-8',
        'Content-Transfer-Encoding: 8bit',
        'Message-ID: <' . bin2hex(random_bytes(12)) . '@' . $cfg['domain'] . '>',
    ];

    // Dot-stuffing: a lone "." on its own line would terminate the message early.
    $safeBody = preg_replace('/^\./m', '..', $body);

    fwrite($fp, implode("\r\n", $headers) . "\r\n\r\n" . $safeBody . "\r\n.\r\n");
    $cmd('', '250');
    @fwrite($fp, "QUIT\r\n");
    fclose($fp);
}

/* ------------------------------------------------------------------ notify */

if (!is_readable(CONFIG_FILE)) {
    logError('Config file missing — pledge stored but not emailed: ' . $email);
    out(true, OK_MESSAGE);
}

$cfg = require CONFIG_FILE;

$body = "A phone was pledged.\n\n"
      . "Email: {$email}\n"
      . 'Time:  ' . date('Y-m-d H:i:s T') . "\n"
      . "IP:    {$ip}\n"
      . 'Saved: ' . ($stored ? 'yes' : 'NO — check the store file') . "\n";

try {
    smtpSend($cfg, 'New Moonlight pledge', $body);
} catch (Throwable $e) {
    // The visitor did nothing wrong and their pledge is saved, so confirm regardless.
    logError('SMTP failed for ' . $email . ' — ' . $e->getMessage());
}

out(true, OK_MESSAGE);
