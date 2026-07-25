# Meridian Moonlight — Project Log

*Session summary: from "I want to build an app" to a live site, a public repo, and a complete
design corpus. Written so that future-you, or a new collaborator, can pick this up cold.*

**Date:** 25 July 2026
**Site:** meridianmoonlight.com
**Repo:** github.com/meridianmoonlight/meridianmoonlight

---

> **Historical record — superseded in part.** This log captures the session that
> produced the first live site and public repo. Several figures in it were later
> found to be wrong and are retracted: the 1.4% / 30M data-centre crossover, the
> 6.6 TOPS fleet average, 40% availability, "never below roughly a third", the
> 2,400 Folding@home-years, and the claim that inference is deterministic so
> honest nodes agree exactly.
>
> Current numbers: [`analysis/NUMBERS.md`](analysis/NUMBERS.md).
> Full list of what changed and why: [WHITEPAPER Appendix B](WHITEPAPER.md#appendix-b-what-we-retract).
>
> It is kept unedited because the reasoning, the rejected ideas, the competitive
> scan, and the problems-and-causes table are all still useful — and because a
> project whose pitch is honesty does not quietly rewrite its own history.

---


## 1. The idea

A free, decentralized AI network with no data center. Compute comes from phones that are already
charging overnight. Capacity grows as people install the app.

**One-line pitch:** *Your phone works for the world while you sleep.*

---

## 2. The first reality check, and the design it forced

The obvious approach — split one large model across many phones — **does not work.** Generating
each token requires data to pass sequentially through every layer of the model, so splitting
across 50 phones means 50 internet hops per token. Petals attempted this with volunteer GPUs on
broadband and still measured seconds per token. On mobile networks with thermal throttling and
aggressive background-task killing, it's dead on arrival.

**The design that does work:** every phone runs a *whole* small model (3–8B, quantized). The
network layer handles routing, verification, and aggregation — never tensor-level splitting.

This single decision shapes everything downstream.

---

## 3. The numbers

All figures are **projections from stated assumptions**, not measurements.

### Assumptions
- ~500M flagship-class devices @ ~12 TOPS sustained (INT8, post-throttle)
- ~1.7B mid-range devices @ ~5 TOPS sustained
- **Fleet average: 6.6 TOPS/device**, ~2.2B capable devices total
- ~40% of the fleet available at any moment (night-side, charging, idle)

### Mobile fleet
| Metric | Value |
|---|---|
| Full-fleet sustained compute | **~14,520 exaOPS** |
| Largest AI data center (reference) | ~200 exaOPS |
| **Crossover point** | **~30.5M devices = 1.39% adoption** |
| Full adoption vs. data center | ~73× |
| H100-class equivalent at full fleet | ~7.26M GPUs |
| Concurrent free AI sessions at full fleet | ~880M |

### Desktop tier (explored late in the session)
| Tier | Devices | Each | Total |
|---|---|---|---|
| Gaming/workstation dGPU | ~250M | ~80 TOPS | ~20,000 exaOPS |
| Apple Silicon Macs | ~70M | ~35 TOPS | ~2,450 exaOPS |
| CPU-only, 16GB+ | ~600M | ~3 TOPS | ~1,800 exaOPS |
| **Desktop total** | ~920M | — | **~24,250 exaOPS** |

**Headline:** ~250M gaming PCs out-compute all 2.2B phones. Combined fleets ≈ **38,800 exaOPS,
~194× the largest data center.** Desktop crossover is **~2.5M machines** — twelve times easier to
reach than the mobile target.

### Research capacity
One night of the full mobile fleet delivers more compute than Folding@home produced in a *year*
at its COVID-era peak. A full year ≈ 2,400 Folding@home-years.

*Caveat carried in the docs: Folding@home is quoted in exaFLOPS, these are INT8 exaOPS. Not
equivalent units — treat as order-of-magnitude.*

---

## 4. Follow-the-moon

Independently arrived at what data centers call "follow-the-moon" scheduling, but better suited
here because supply migrates automatically.

Demand peaks during working hours; supply peaks overnight — an 8–14 hour offset. Because night
circles the planet continuously, **network availability never drops below roughly a third of the
fleet at any hour UTC.** There is no off-peak.

Practical note: China's cross-border filtering makes its device pool unreliable. Realistic
night-side pairs are US↔India/SE Asia/Europe and Europe↔Americas.

---

## 5. Ideas explored and rejected

**Fiber-optic delay-line storage.** Using in-flight light in deployed fiber as memory. Ran the
numbers: ~30–300 PB total if you commandeered every strand on Earth — less than one hyperscale
data center, volatile, and consuming the planet's entire telecom capacity. Dropped. The real
constraint was never storage; it's inter-chip latency, which no storage scheme fixes.

**Token / crypto economy.** Rejected deliberately. It's what every competitor already is, it
reintroduces the Sybil incentive the security model relies on being absent, and it forfeits the
one unoccupied position in the market.

---

## 6. Competitive landscape (as of mid-2026)

| Project | Status |
|---|---|
| **Acurast** | Furthest along. 250,000+ smartphone nodes, 175+ countries, TEE-based. Mainnet + token Jan 2026. "Milestone Cray" (Feb 2026) added local device clustering. 225k nodes on Base, June 2026. |
| **Destra Edge** | Mobile inference nodes with overlapping execution for verification. |
| **Pocket Network / NodeGhost** | Decentralized routing + OpenAI-compatible gateway. Ran a full AI stack on TEE smartphones with no cloud server. |
| **Exo Labs** | Pivoted to local clusters of nearby machines (MLX on Apple Silicon) — same physics lesson. |
| **BOINC / Folding@home** | Decades old, PC-only, no LLM inference. No mobile-first successor. |

**The gap:** every serious player is crypto/DePIN, using token rewards to solve participation.
None has escaped that niche. **Nobody occupies the position of "free AI a normal person installs
because the mission is good."** That's the opening.

**Strategic fork left open:** build the stack independently, or ride Acurast's protocol as the
compute layer and own the consumer app and mission. Not yet decided.

---

## 7. Why developers can't just embed this quietly

1. **App store policy** — Apple and Google ban unrelated background compute (dates to the 2018
   crypto-mining bans). Must be opt-in, disclosed, and the app's actual stated purpose.
2. **OS throttling** — iOS gives background apps seconds before suspension. Sustained work
   realistically happens only when charging and idle, mostly on Android.
3. **Consent and law** — using someone's device without clear consent is legally botnet territory.

Which is the strategic insight: **the moat isn't technology, it's trust and participation.**

---

## 8. Security architecture

### The foundation
**The network never executes arbitrary code on a volunteer's phone.** Inference only, from a
signed model allowlist. A job is a prompt plus a model ID — never a script, binary, or container.

This eliminates mining, password cracking, malware, and proxy abuse *structurally* rather than by
policy. Competitors run general-purpose runtimes (Node.js, WASM, containers); that flexibility is
the attack surface. This trade is permanent.

### Defense layers
| Layer | Mechanism |
|---|---|
| Who can join | Device attestation (Play Integrity, DeviceCheck) |
| Is the work real | Redundant execution across 2–3 nodes; deterministic replay at temp 0 |
| Catching liars | Canary tasks with known answers, mixed in indistinguishably |
| Earned standing | Reputation from zero, accruing over weeks |
| Model integrity | Content-addressed, hash-verified weights |
| No prize to win | Non-transferable credits — remove the money, remove the motive |

### Desktop tier — no attestation available
Two reframes make it tractable:

1. **Sybil buys identity, not capacity.** A thousand VMs on one machine still have one machine's
   compute. Combined with non-transferable capped credits, farming yields nothing. Collapses the
   threat list to two items: poisoned results and prompt harvesting.
2. **Verify the work, not the worker.** Deterministic inference means any result can be
   re-derived and checked exactly.

Key mechanism: **diversity constraints** — redundant copies of a job never go to nodes sharing a
subnet, ASN, region, or join cohort. A VM farm fails all four at once.

Partial attestation *does* exist: TPM 2.0 (mandatory on Windows 11) and App Attest (Apple
Silicon). Produces a trust ladder rather than a binary. Unattested nodes are never excluded —
just never trusted alone.

### Stated honestly
- A node operator **can read the prompts their device processes.** Inference needs plaintext in
  memory. Only TEEs fix it, and coverage is patchy on mid-range hardware.
- Attestation excludes rooted and custom-ROM devices — a real cost, worth revisiting.
- A well-resourced adversary with genuinely distributed infrastructure can eventually poison some
  results. No open network solves this.
- **No external audit exists yet.** Everything is intent until someone tries to break it.

---

## 9. The compute economy

Rejected tokens; adopted **non-transferable compute credits**.

- **Earned by hours of reliable availability, not throughput.** A four-year-old phone earns the
  same as a flagship. Paying by performance would hand the most access to those who need free AI
  least — a quiet betrayal of the mission.
- **Spent on** queue priority, larger models, longer context, and submitting your own batch job.
  That last one is the real economy: a researcher with no budget earns compute instead of buying it.
- **Cannot be** bought, sold, transferred, or cashed out. Decay on ~90-day half-life so they never
  become an asset. **Never votes** — that would build a plutocracy and attract securities scrutiny.
- **The free floor is unconditional.** Credits buy priority and headroom, never access. If the free
  tier ever degrades to make credits attractive, the project has failed.
- **Real money lives on a separate ledger.** Institutions buy overnight batch capacity in ordinary
  currency, from surplus only, on a public ledger. Contributors are never paid — which keeps them
  volunteers, not unlicensed contractors.

---

## 10. Naming

`MERIDIAN` alone was taken and the good domains were expensive. Settled on **Meridian Moonlight**:
the *meridian* is the longitude line the compute follows as night rotates; to *moonlight* is to
work a second job after dark. Shortened to "Moonlight" in casual use.

Domain **meridianmoonlight.com** — no hyphens anywhere, in the domain, repo slug, or handles.
*(Worth buying obvious misspellings and 301-redirecting them.)*

---

## 11. Build state

### Live
- **Website** at meridianmoonlight.com, hosted on Namecheap cPanel (not GitHub Pages)
- **Repo** public at github.com/meridianmoonlight/meridianmoonlight
- **Email** on Namecheap Private Email, Launch plan (1 mailbox, 10 aliases)

### The website
Single-file `index.html`, no build step, no dependencies.

- **Signature element:** a live terminator band under the hero — night sweeps 360° of longitude
  and device dots ignite amber as darkness reaches them, with a UTC/availability readout. Runs a
  24h cycle every 45 seconds; freezes at real current hour for reduced-motion users.
- **Interactive simulator:** drag adoption from 1K to 2.2B devices, watch sustained compute,
  GPU-equivalents, and concurrent sessions update against a data-center reference line. A verdict
  line rewrites itself as thresholds are crossed.
- **Palette:** deep night sky (`#0A0E20`), moonlight text, charging-amber accent, daylight cyan.
- **Type:** Archivo (expanded, infrastructure signage), Public Sans (the US design system's
  public-service face), JetBrains Mono for readouts.
- **Sections:** hero → 1.4% crossover + simulator → how it works → what it's for → honest limits →
  no-token promise → compute economy → roadmap → join → keeping it alive.

### Backend
- `subscribe.php` — validates, honeypot, rate-limits (12/hr/IP), writes pledges to a CSV **above**
  the web root, notifies via **SMTP through Private Email** (not `mail()`, which fails SPF).
- `moonlight-config.php` — credentials, stored above `public_html`, chmod 0600.
- `.htaccess` — HTTPS redirect, www→apex canonical, security headers, blocks dotfiles and data
  files, exempts `.well-known/` so AutoSSL can validate.

### Documents
| File | Contents |
|---|---|
| `README.md` | Repo front page with diagrams and projections |
| `VISION.md` | Full vision — problem, architecture, principles, constraints |
| `ROADMAP.md` | Repo structure, tech stack, milestones, risk register |
| `RESEARCH.md` | Timeline + what maximum compute unlocks for science |
| `THREAT_MODEL.md` | Security architecture and honest limits |
| `DESKTOP_SECURITY.md` | Trusting nodes that can't be attested |
| `ECONOMY.md` | Compute credits design |
| `PROJECT_LOG.md` | This file |

### Visuals
- Six matplotlib figures (compute vs adoption, concurrent sessions, follow-the-moon, comparison,
  timeline, research capacity)
- Three SVG system diagrams (architecture, security layers, economy flow) + PNG versions

---

## 12. Roadmap

| Phase | Scale | Ships |
|---|---|---|
| **M0** | 1 device | Phone runs a 3B model on its charger, reports compute to a coordinator |
| **M1** | ~100 | Routed inference, redundant verification, reputation, live node map |
| **M2** | ~10K | Region-aware routing, measured availability curve, first science batch job |
| **M3** | 100K–1M | Protocol spec v1.0, third-party nodes, federated learning, governance |
| **M4** | 1M → 30M+ | Full P2P discovery, institutional research program, passes largest data center |

**Tech stack:** llama.cpp (GGUF Q4) · Llama 3.2 3B / Qwen 2.5 3B / Phi-3.5 · Kotlin (Android
first) · Node.js + TypeScript coordinator · React + Vite dashboard · redundant execution for
verification.

**Open reordering question:** desktops are better nodes in nearly every dimension — more RAM,
real GPUs, active cooling, mains power, **no app store and no background-execution limits.** M0
may be faster and more demonstrable as a desktop client, with mobile remaining the scale story.

---

## 13. Problems hit, and their causes

Recorded so they don't get re-debugged later.

| Symptom | Cause |
|---|---|
| README rendered as raw CSS | `index.html` contents pasted into `README.md`; `index.html` got `.gitignore` contents. Upload files, don't paste them. |
| Broken image in README | Root-level PNGs corrupted by the first bad upload; clean copies live in `docs/figures/` |
| GitHub Pages 500 error | GitHub-side outage affecting Actions (Pages builds run through Actions) |
| Site "connection timed out" | Home IP auto-banned by the host firewall (cPHulk/CSF) after rapid troubleshooting requests. Site was fine for everyone else. |
| SSL inactive | AutoSSL can't issue until DNS resolves; `.htaccess` HTTPS redirect must stay commented until the cert exists |
| Form sent nothing | cPanel treated the domain as a local mail exchanger, and `mail()` sends from a server SPF doesn't authorize. Fixed by Remote Mail Exchanger + SMTP relay. |

---

## 14. Open items

**Immediate**
- [ ] Confirm the pledge form actually delivers (check `moonlight-errors.log` above `public_html`)
- [ ] Verify HTTPS is active, then uncomment the redirect block in `.htaccess`
- [ ] Add `security@meridianmoonlight.com` as a mailbox alias — it's cited in `THREAT_MODEL.md`
- [ ] Add SPF, DKIM, and DMARC records at Namecheap (`v=spf1 include:spf.privateemail.com ~all`;
      DKIM host `privateemail._domainkey`; DMARC at `p=none` to start)
- [ ] Fix README figure paths to `docs/figures/` and delete the corrupted root PNGs
- [ ] Ask Namecheap to whitelist the home IP permanently

**The one that matters most**
- [ ] **Record the M0 demo.** Phone on a charger, answering a prompt from the PC. Sixty seconds.
      In a space full of whitepapers, a video of something running is what turns a skeptic into a
      contributor. Put it in the hero before sharing the link anywhere.

**Design decisions still open**
- [ ] Desktop-first M0, or stay mobile-first?
- [ ] Build the stack independently, or ride Acurast's protocol and own the consumer layer?
- [ ] `NODE_TIERS.md` — capability tiers across workstation / laptop / phone (not yet written)
- [ ] Extend the site simulator to model both mobile and desktop fleets
- [ ] Should batch-job submission require identity verification?
- [ ] Is 90 days the right credit half-life for irregular contributors?

**Launch, when the demo exists**
- r/LocalLLaMA · Hacker News (Show HN) · BOINC and Folding@home forums · r/selfhosted
- Lead with the working demo and the honest-constraints section. Let them attack the math — if it
  survives, those are the first hundred nodes.

---

## 15. The through-line

Every decision in this session came back to the same principle: **publish the weak points first.**

The honest-limits section, the stated assumptions on every chart, the unit-mismatch caveat on the
Folding@home comparison, the admission that node operators can read prompts, the note that no
audit exists yet. In a field crowded with token projects making unfalsifiable claims, being the
one that says *here's what physics forbids* is not a weakness in the pitch.

It's the whole pitch.
