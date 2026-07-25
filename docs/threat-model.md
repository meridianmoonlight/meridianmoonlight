# Threat model & security architecture

How the network defends itself, what it deliberately cannot do, and when each defence lands.

Companions: [docs/desktop-security.md](desktop-security.md) for the unattested tier, [docs/task-types.md](task-types.md) for the catalogue Layer 0 forces, [ARCHITECTURE.md](../ARCHITECTURE.md#5-verification) for verification mechanics.

---

## The core design decision

**The network never executes arbitrary code on a volunteer's machine.**

This is the single most important security property and everything else follows from it. Nodes run **inference and a fixed set of audited task types only**, from a signed allowlist. A job is a prompt plus a task-type ID — never a script, never a binary, never a container.

That one constraint eliminates the entire category of attacks people rightly fear from volunteer computing:

- No crypto mining on someone's battery
- No password cracking or hash breaking
- No malware execution or lateral movement
- No using volunteer IPs as a proxy network
- No arbitrary file or network access from a job

Competing networks run general-purpose runtimes — Node.js, WASM, containers — to be flexible. **That flexibility is precisely the attack surface.** Moonlight trades capability for safety here, permanently, and on **every tier**. There is no privileged desktop tier that runs submitted code.

Scientific batch work is supported the same way: as a fixed set of audited task types, not as submitted code. The cost of that — a researcher cannot bring a novel simulation — is stated in full in [task-types.md](task-types.md#what-that-costs).

---

## Assets and adversaries

| Asset | Why an attacker wants it |
|---|---|
| Result integrity | Poison scientific output; discredit the network |
| Model integrity | Steer the shared model's behaviour |
| Participant privacy | Usage patterns, timing, prompt content |
| Volunteer devices | Free compute for someone else's purpose |
| The coordinator | Single point of control during the centralised phase |
| The project's reputation | One incident is sufficient to end a volunteer network |

**Out of scope:** an adversary with physical access to an unlocked participant device, and a compromised host OS. We cannot defend those and won't pretend to.

### What the absence of money already removes

Worth stating early because it does more work than any single control: **there is no token, no payout, and no transferable credit.** Nearly every attack on comparable networks is economically motivated. Removing the money removes most of the motive — and it is why [DESKTOP_SECURITY](desktop-security.md#reframe-1-sybil-buys-identity-not-capacity) can narrow a long threat list down to two real items.

---

## 1. Protecting volunteers

The people donating hardware take the most risk and get the least attention in most designs. They come first here.

| Threat | Defence |
|---|---|
| Device abused for illegal work | Layer 0 — inference and audited task types only. No general compute path exists. |
| Battery, heat, or data cost | Hard client-side gate: charging + Wi-Fi + screen off + battery above 80% + thermal nominal. Backoff pauses work if the device warms. Enforced, not requested politely. |
| Volunteer's address tied to a request | Requests are relayed; node and requester never learn each other's addresses. Nodes are never told who asked. |
| Legal exposure from content processed | Content policy enforced **at dispatch, not at the node** — volunteers should never be the filter. Volunteers may opt out of open request-serving entirely and contribute only to vetted research batch jobs. |
| Malicious clone of the app | Signed official builds with reproducible-build instructions. The protocol rejects clients without a valid build signature. |
| Someone can't get out | One switch, no dark patterns, immediate effect. Uninstalling is always sufficient. |

**Consent stays explicit.** Opt-in at install, re-confirmed after any release that changes what work the device may accept — including a new task type — and revocable without penalty.

---

## 2. Verification: how we know the work is real

A node that returns plausible garbage while claiming credit is the most likely attack, because it is the cheapest.

### The determinism correction

Earlier drafts of this project claimed that *"inference at temperature 0 with a fixed seed is deterministic, so any result can be re-derived and checked exactly."* **That is true on identical hardware and false across a heterogeneous fleet**, and the distinction matters because the fleet is the whole point.

Different SoCs, different kernels, different thread counts, and different quantisation implementations change floating-point reduction order. When two logits are close, argmax flips. Over hundreds of tokens, divergence between two honest nodes is near-certain.

Building verification on cross-node exact match would therefore have produced constant false accusations against honest nodes and a security model that fails in production rather than in review.

### What we do instead

Verification rests on the two mechanisms that work regardless:

**Canary tasks — primary.** Jobs with known-correct answers, mixed in indistinguishably from real work. A node cannot tell a canary from a paying job, so the only way to pass reliably is to actually compute. New and unattested nodes get a higher canary rate. Failing one forfeits accrued standing and triggers review of that node's recent output.

**Coordinator re-derivation — primary.** For any result, the coordinator can silently re-run the job itself or on a high-reputation node. Cheap for small models, used as a random audit, so an attacker never knows which of their answers is being checked.

And two that are scoped to where they hold:

**Exact match within a hardware cohort.** Nodes are grouped by SoC, build, and thread configuration. Inside a cohort, bit-exact comparison is valid and free, so we use it.

**Semantic tolerance across cohorts.** Comparison against a published, versioned similarity threshold. Disagreement escalates to a trusted reference node rather than penalising either party immediately.

**Numeric task types verify best of all.** `infer.embed`, `infer.classify`, `infer.extract`, and every `sci.*` type produce outputs comparable exactly or within a stated numeric tolerance across *any* hardware. This is a real advantage of batch and scientific work over open-ended chat, and it is why [the desktop tier's trust model is more tractable](desktop-security.md) than its weaker attestation would suggest.

**Sampling is published.** Verification at 3× redundancy costs 3× the compute, so we sample rather than check everything, and the rate is sent to nodes and published. An unpublished sampling rate is indistinguishable from no verification.

**M0 tests reproducibility as a fast path, not a dependency.** If bit-exactness turns out to hold across some hardware pairs, those become cohorts and verification gets cheaper. If it holds nowhere, nothing above changes.

---

## 3. Network integrity

### Sybil resistance

- **Device attestation** on mobile — Play Integrity, DeviceCheck. Proves genuine hardware running an unmodified official build. The strongest single control available, and it makes large fake fleets expensive rather than free.
- **Reputation earned slowly.** New nodes start at zero, receive only redundantly verified work, and gain standing over weeks. Influence cannot be bought, only waited for — and waiting is visible.
- **No financial reward.** See [above](#what-the-absence-of-money-already-removes).
- **Diversity constraints on assignment.** Redundant copies of a job never go to nodes sharing a subnet, ASN, region, or join cohort. A VM farm fails all four at once. Detailed in [desktop-security.md](desktop-security.md#diversity-constraints-on-node-selection).

**Residual risk. This is not solved.** Sybil resistance has never been achieved without either a trusted identity registry or a costly stake, and we have ruled out stake. We bound the damage rather than preventing the attack. Anyone claiming to have solved this cheaply should be read skeptically, including us.

### Poisoned models

Model files are content-addressed and hash-verified at load; a modified model fails before a single token is produced. Attestation confirms the client binary is official, so the loader itself can't be patched. Cross-node comparison catches drift a hash check somehow misses.

### Poisoned results

An attacker controlling enough of a job's redundancy set can make all copies agree on a wrong answer — an **eclipse attack**, and the genuine danger on the unattested tier. Countered by diversity constraints, unpredictable assignment, coordinator re-derivation, canaries weighted toward new nodes, and escalating redundancy for high-value work. Full treatment in [desktop-security.md](desktop-security.md#threat-1--poisoned-results).

### Model poisoning via federated updates

Deferred to M3 specifically so verification and reputation have real operating history first. Mitigations: robust aggregation discarding outliers, per-update norm clipping, holdout evaluation gates before promotion, staged rollout with automatic rollback, contribution weighted by reputation.

**Residual risk.** A patient attacker with many reputable nodes contributing subtly biased updates over a long period is hard to detect. Holdout evaluation catches capability regressions, not narrow targeted bias.

### Coordinator compromise

The single point of failure until M3, and the honest weak spot.

- The allowlist of permitted models and task types ships **in the client**, not from the server. A compromised coordinator still cannot make a device run something new.
- Nodes verify coordinator signatures; a hijacked coordinator can't silently issue new job types.
- Model hashes are verified client-side; a malicious manifest is rejected.
- Nodes enforce their own contribution gate locally. **The coordinator can never instruct a device to override its own gate** — a hard protocol invariant.
- M3 replaces central dispatch with peer discovery, and the published protocol means anyone can run a competing coordinator. That is the real structural mitigation.

---

## 4. Protecting the people asking

- Prompts encrypted in transit between requester and assigned node.
- Nodes are stateless: nothing written to disk, memory cleared after each job.
- The coordinator sees routing metadata, not content.
- No account required to ask, so there is no profile to leak.
- **No session continuity.** Consecutive turns of a conversation are deliberately routed to different nodes, so no single operator sees a whole thread.

---

## 5. Abuse of the network as a service

- Requesters rate-limited, with proof-of-work at higher volumes so bulk abuse costs the abuser real compute.
- Content policy enforced at dispatch, never at the node.
- Research batch jobs accepted only from verified institutional submitters with published identities.
- Task types are bounded in runtime, memory, and output size, so no single job can monopolise a device.

---

## 6. What this design cannot do

The honest limits are the credible part.

- **A node operator can read the prompts their machine processes.** Inference requires plaintext in memory. Only hardware TEEs fix this, and coverage is inconsistent across the mid-range devices that make up most of the fleet. Mitigation is structural rather than absolute: no requester identity, no session continuity, no ability to choose whose work you receive. **Users are told this plainly rather than promised privacy the architecture cannot deliver** — including on the website, not buried here.
- **Attestation excludes rooted and custom-ROM devices.** A real cost that locks out some of the most technically capable volunteers. Right trade at this scale; should be revisited, not defended reflexively.
- **Sybil resistance is bounded, not solved.** See above.
- **A well-resourced adversary with genuinely distributed infrastructure** — real machines across many providers and regions, behaving honestly for months — can eventually earn enough standing to poison some results. Redundancy and re-derivation limit the blast radius. No open network solves this.
- **Verification sampling means most work is unchecked.** The rate is published for exactly that reason.
- **Behavioural fingerprinting is an arms race**, never a solved problem.
- **No external audit exists yet.** Until one does, treat every claim here as intent rather than proof.

---

## 7. What lands when

| Phase | Security work |
|---|---|
| **M0** | Signed builds. Hard-coded contribution gate with no remote override. Layer 0 client with no code-execution path. Reproducibility measured across machines — as a fast path, not a dependency. |
| **M1** | Redundant execution, cohort-scoped exact match, semantic tolerance across cohorts, reputation scoring, coordinator request signing, TLS everywhere. |
| **M2** | Attestation (mobile) and TPM/App Attest (desktop). Canary tasks with tier weighting. Diversity constraints on assignment. Coordinator re-derivation audits. Dispatch-level content policy. Requester rate limits and proof-of-work. |
| **M3** | Published threat model for outside review, first external audit, peer discovery to remove coordinator centrality, reproducible builds, attested-only routing option for sensitive requests. |
| **Ongoing** | Public disclosure policy, security contact, incident transparency. Every incident written up publicly, including the embarrassing ones. |

---

## Reporting a vulnerability

Email **security@meridianmoonlight.com**, or use [private vulnerability reporting](../../security/advisories/new). Please give a reasonable window before public disclosure. Findings are credited unless you prefer otherwise, and write-ups are published regardless of how bad they make the project look.

See [SECURITY.md](../SECURITY.md) for scope and the list of known-unsolved problems — we would rather tell you than have you spend a weekend rediscovering them.
