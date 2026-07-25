# Your asks — everything that needs you

Ordered by what blocks what. Nothing here needs code.

The repo is the source of truth; `deploy/` is exactly what goes on the host.

---

## 1. Upload the site (10 minutes)

Everything in **`deploy/public_html/`** goes into `public_html`:

```
index.html          whitepaper.html     .htaccess           og.png
robots.txt          sitemap.xml         figures/            diagrams/
meridian-moonlight-whitepaper.pdf
```

That is the whole site. **There is no PHP, no database, and nothing above the web root any more** — the pledge form is gone, replaced by a link that opens the visitor's email app. Nothing is stored and nothing can leak.

**In cPanel File Manager, turn on Settings → Show Hidden Files** or `.htaccess` is invisible.

**Delete any parking placeholder** (`default.html`, `index.php`) first.

### Order matters for SSL

The HTTPS redirect block in `.htaccess` is **already commented out**. Leave it that way until the certificate exists:

1. Upload with the redirect commented
2. Confirm `http://meridianmoonlight.com` loads
3. cPanel → SSL/TLS Status → **Run AutoSSL**
4. Confirm `https://` works
5. *Then* uncomment the four redirect lines

---

## 2. Make sure email actually works

The site no longer sends anything, but people will now email `hello@` directly — so the mailbox has to receive reliably, and your replies have to not land in spam.

- [ ] **cPanel → Email Routing → set the domain to Remote Mail Exchanger.** Otherwise cPanel tries to deliver locally, finds no mailbox, and silently drops incoming mail.
- [ ] **Add DNS records** at Namecheap → Advanced DNS. **Never delete the MX records** — you are adding, not replacing:

| Type | Host | Value |
|---|---|---|
| TXT | `@` | `v=spf1 include:spf.privateemail.com ~all` |
| TXT | `_dmarc` | `v=DMARC1; p=none; rua=mailto:hello@meridianmoonlight.com` |
| TXT | `privateemail._domainkey` | *(copy from the Private Email dashboard)* |

- [ ] **Test it.** Send yourself a message from an outside address, and reply to it. Both directions need to work.

---

## 3. Add two mailbox aliases

Both are cited in published documents, so they need to exist before anyone reads them:

- [ ] **security@meridianmoonlight.com** — cited in `SECURITY.md` and `docs/threat-model.md`
- [ ] **conduct@meridianmoonlight.com** — cited in `CODE_OF_CONDUCT.md`

You have 10 aliases on the Private Email Launch plan; aliases forward to `hello@`, which is fine.

---

## 4. Push the repo

The `OWNER` placeholder is resolved — every link now points at `github.com/meridianmoonlight/meridianmoonlight`.

```bash
cd "E:/Project Meridian/meridian"
git remote add origin https://github.com/meridianmoonlight/meridianmoonlight.git
git push -u origin main
```

I have **not** pushed anything. Three commits are waiting locally.

**Before you push, know that this replaces the current repo contents** — the live README carries the retracted numbers, and this rewrite corrects them.

Then in the GitHub UI:

- [ ] Set the repo description and the `meridianmoonlight.com` link
- [ ] Enable **Issues** and **Discussions**
- [ ] Create milestones **M0–M4** and paste the issues from `docs/MILESTONES.md`
- [ ] Pin **"Check our math"** (#34) and **"Open questions register"** (#35)
- [ ] Turn on **private vulnerability reporting** (Settings → Code security)

---

## 5. Housekeeping from your own log

- [ ] Ask Namecheap to **permanently whitelist your home IP** — the host firewall auto-banned you once already during troubleshooting.
- [ ] Delete the corrupted root-level PNGs in the old repo if any survive; figures now live in `docs/figures/` and are generated.
- [ ] Buy the obvious misspellings of the domain and 301 them.

---

## 6. The one that matters most

- [ ] **Record the 60-second M0 demo.** A machine on a charger, answering a prompt typed on another machine.

In a field full of whitepapers, a video of something running is what turns a skeptic into a contributor. **It goes in the hero before the link is shared anywhere.** It is issue #0 in `docs/MILESTONES.md` for a reason.

The desktop client gets you there fastest — no app-store review, no background-execution limits, no thermal ceiling.

---

## Decisions I made on your behalf

Flagging these because they're judgement calls, not mechanical ones. All are reversible.

| Decision | Why | Where |
|---|---|---|
| Ship the diagrams as **SVG, not PNG** | The PNGs in your zip still contain the wrong determinism text. SVG renders on GitHub, is sharper, and can't drift from the corrected source. | `docs/diagrams/` |
| Simulator now plots against **Folding@home**, not the data-center line | The data-center comparison is the retracted claim. Plotting it would have made the interactive centrepiece display the error we're retracting. | `site/index.html` |
| Reference line changed from **red to cyan** | Your simulator used `rgba(196,78,82)` for the data-center line — red, which you can't reliably distinguish. | `site/index.html` |
| **Deleted `subscribe.php` and its config** rather than leaving them unused | The pledge is gone, so the backend is dead weight — and an unused PHP endpoint with a credentials file is a liability, not a spare part. Git history keeps them. | `deploy/` |
| Kept your **ROADMAP.md content** but superseded it with `docs/MILESTONES.md` | Yours was the original outline; MILESTONES is issue-ready and covers both tiers. | `docs/MILESTONES.md` |
| Desktop availability modelled **lower than mobile** (19.6% vs 25.7%) | People plug phones in and switch PCs off. This is the one axis where desktops lose, and omitting it would have overstated the tier. | `analysis/compute_model.py` |

---

## What I did not do

- **Did not push to GitHub or upload to the host.** Both are outward-facing and yours to trigger.
- **Did not create a GitHub organisation, milestones, or issues** — needs your account.
- **Did not touch DNS, email, or SSL.**
- **Did not delete anything** from the live site or repo.

---

## Still unresolved, and genuinely open

These aren't blockers, but they're the things I'd want decided before M1:

1. **Ride Acurast's protocol, or build the stack?** They have 250k+ nodes and a working TEE network. Owning the consumer layer and mission on top of someone else's compute layer is a real option, and your log left it open.
2. **Should batch-job submission require identity verification?** It's the most abusable credit spend.
3. **Is 90 days the right credit half-life** for irregular contributors?
4. **Is 25% the right single-buyer revenue cap?** I picked it; it's a guess.
5. **Who audits the public ledger** before there's money to pay an auditor?
