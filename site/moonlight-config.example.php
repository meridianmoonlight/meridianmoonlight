<?php
/**
 * Meridian Moonlight — mail configuration
 *
 * PUT THIS FILE ONE LEVEL ABOVE public_html.
 * Correct:   /home/yourcpaneluser/moonlight-config.php
 * WRONG:     /home/yourcpaneluser/public_html/moonlight-config.php
 *
 * Above the web root, nobody can reach it over HTTP even if PHP breaks.
 * Inside public_html, a PHP misconfiguration could serve your password as plain text.
 *
 * Rename this file to: moonlight-config.php
 * Then set permissions to 0600 (File Manager → right-click → Change Permissions:
 * tick only Read and Write for User).
 */

declare(strict_types=1);

return [
    // Namecheap Private Email SMTP.
    // Port 465 uses implicit SSL. If your host blocks it, use 587 instead —
    // the script switches to STARTTLS automatically.
    'host' => 'mail.privateemail.com',
    'port' => 465,

    // Your full mailbox address and its password.
    // This must be a real mailbox, not an alias — aliases can't authenticate.
    'user' => 'hello@meridianmoonlight.com',
    'pass' => 'PUT-YOUR-MAILBOX-PASSWORD-HERE',

    // Envelope addresses. Keeping 'from' identical to 'user' is what makes
    // SPF and DKIM line up.
    'from' => 'hello@meridianmoonlight.com',
    'to'   => 'hello@meridianmoonlight.com',

    // Used for the Message-ID header and the SMTP greeting.
    'domain' => 'meridianmoonlight.com',
    'helo'   => 'meridianmoonlight.com',
];
