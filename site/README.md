# site/ — meridianmoonlight.com

Static HTML plus one PHP endpoint. No framework, no bundler, no build step on the host.

**Hosting is Namecheap cPanel, not GitHub Pages.** The repo is the source of truth; the host serves a copy. Edit here, commit, *then* upload — that way there is always a version history and a way to roll back.

## What goes where

Four files into `public_html`:

| File | Notes |
|---|---|
| `index.html` | Hand-written. Self-contained apart from Google Fonts. |
| `whitepaper.html` | **Generated** from `../WHITEPAPER.md` by `build.py`. Do not edit. |
| `subscribe.php` | Pledge handler — validates, honeypot, rate limits, stores, emails via SMTP |
| `.htaccess` | HTTPS redirect, www→apex, security headers, blocks data files |

Plus `figures/`, `og.png`, `robots.txt`, `sitemap.xml`.

And **one level above** `public_html`, in the home directory:

| File | Notes |
|---|---|
| `moonlight-config.php` | Renamed from `moonlight-config.example.php`. Mailbox password. **chmod 0600.** |

### Why the config sits outside the web root

It holds the mailbox password. Above `public_html` nobody can reach it over HTTP even if PHP breaks. Inside `public_html`, one misconfiguration serves the password as plain text.

`subscribe.php` also writes `moonlight-pledges.csv` and `moonlight-errors.log` **above** the web root for the same reason, and `.htaccess` denies `.csv`/`.log` as a second line of defence.

## Rebuilding

```bash
pip install numpy matplotlib markdown

python analysis/compute_model.py         # figures + numbers (run first if the model changed)
python analysis/participant_economics.py # the pay-contributors costing
python site/build.py                     # whitepaper.html + copies figures into site/
python site/make_og.py                   # og.png
```

`build.py` renders the markdown rather than duplicating it, so the published page cannot drift from the repository document. If you find yourself editing `whitepaper.html` by hand, edit `WHITEPAPER.md` and rebuild instead.

## The model constants are duplicated on purpose

`index.html` contains a JavaScript port of the availability curve and the tier throughput figures from `analysis/compute_model.py` — same cluster weights, same smooth night window, same normalisation. That is what makes the live readout and the simulator agree with the published numbers instead of being decorative.

**If you change one, change both.** Verified to agree:

| | night peak | mean | min | max |
|---|---|---|---|---|
| Python | 60.1% | 25.7% | 14.1% | 40.8% |
| JavaScript | 60.1% | 25.7% | 14.1% | 40.8% |

The simulator additionally uses: mobile 0.299 TFLOPS / 12.3 tok/s / 25.7% availability; desktop 2.983 TFLOPS / 26 tok/s / 19.6% availability; Folding@home peak 2.4 exaFLOPS; 15 tok/s per active conversation.

## Order matters for SSL

Leave the HTTPS redirect block in `.htaccess` **commented out** until AutoSSL has issued the certificate. Forcing HTTPS before the cert exists redirects the site into an error that is hard to see past.

1. Upload with the redirect commented
2. Confirm `http://meridianmoonlight.com` loads
3. cPanel → SSL/TLS Status → Run AutoSSL
4. Confirm `https://` works
5. Uncomment the four redirect lines

## Email

Mail is on Namecheap Private Email, not the cPanel server. Two settings make outbound work:

1. **cPanel → Email Routing** → set the domain to **Remote Mail Exchanger.** Otherwise cPanel tries to deliver locally, finds no mailbox, and drops the message.
2. `subscribe.php` sends via authenticated **SMTP**, not PHP `mail()` — which sends from a server your SPF record doesn't authorise.

DNS records to add at Namecheap → Advanced DNS (**never delete the MX records**):

| Type | Host | Value |
|---|---|---|
| TXT | `@` | `v=spf1 include:spf.privateemail.com ~all` |
| TXT | `_dmarc` | `v=DMARC1; p=none; rua=mailto:hello@meridianmoonlight.com` |
| TXT | `privateemail._domainkey` | *(copy from the Private Email dashboard)* |

## Accessibility notes

- **No red as a signal colour** anywhere — figures, simulator, or UI. The simulator's reference line is cyan.
- The hero animation respects `prefers-reduced-motion`: it holds at the current real UTC hour and offers an explicit **Play animation** button, so it never reads as broken. This is why the animation appears static on Windows with "Show animations" turned off.
- Tables scroll inside their own containers; the page body never scrolls horizontally, verified to 375px.
- The canvases carry `aria-label` descriptions.
- The pledge form degrades to a normal POST if `fetch` is unavailable, and validates before submitting.

## Troubleshooting

| Symptom | Cause |
|---|---|
| Site times out for you but works on mobile data | Your IP got auto-banned by the host firewall after rapid requests. Ask support for a permanent whitelist. |
| 500 error after upload | `.htaccess` — usually the HTTPS redirect firing before the certificate exists. Rename to `.htaccess.off` to confirm. |
| SSL stays inactive | DNS must resolve first, and `.well-known/` must not be redirected. This `.htaccess` already exempts it. |
| Form confirms but no email | Check `moonlight-errors.log` above `public_html` — it records the exact SMTP failure. If the connection fails, change the config port from 465 to 587. |
| Parking page instead of the site | A leftover Namecheap CNAME for `@` or a URL Redirect record. Delete both. |
