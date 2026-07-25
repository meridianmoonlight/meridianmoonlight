# Securing the desktop tier

*How to trust nodes you cannot attest.*

The desktop tier matters more than its novelty suggests: it carries **85% of the network's scientific capacity**, and reaches Folding@home parity with roughly [1.3 million discrete-GPU machines against 31 million phones](../analysis/NUMBERS.md#the-desktop-tier). It is also the tier we can prove the least about.

---

## The problem, stated plainly

On mobile, Play Integrity and DeviceCheck prove two things: this is real hardware, and it's running our unmodified build. That single control does most of the anti-Sybil work.

On desktop, no equivalent exists in the general case. Anyone can spin up a thousand VMs that each look like a distinct machine, patch the client binary, or lie about their hardware. The strongest defence in the mobile threat model simply isn't available.

So the desktop tier has to earn trust a different way.

---

## Reframe 1: Sybil buys identity, not capacity

This is the load-bearing insight.

An attacker running a thousand VMs on one machine has **the compute of one machine**. They can multiply their *identities* freely, but not their *throughput*. Every fake node they add makes each one slower and more obviously so.

That constrains what a Sybil attack can actually achieve here:

| Attack goal | Does Sybil help? |
|---|---|
| Farm credits for profit | **No.** Credits are non-transferable, non-sellable, capped per node per day, and decay. A thousand accounts' worth of stranded credits is worth exactly nothing. |
| Consume network capacity | **No.** Nodes supply capacity; they don't consume it. |
| Gain governance influence | **No.** Credits are explicitly not votes. |
| **Poison results** | **Yes — this is the real threat.** |
| **Harvest prompts at scale** | **Yes — the other real threat.** |

Two threats, not twenty. [The absence of a token economy](threat-model.md#what-the-absence-of-money-already-removes) already eliminated most of the list. Design against the two that remain.

---

## Reframe 2: verify the work, not the worker

You never have to trust a node's claim about itself — only its output, which is checkable. That flips the security model from *identity-based* (who are you?) to *behaviour-based* (is your work correct?). Behaviour-based verification doesn't care whether a node is a real desktop, a VM, or a toaster.

### The correction that makes this actually work

An earlier version of this document justified the reframe by asserting that *"inference at temperature 0 with a fixed seed is deterministic, so any result can be independently re-derived and checked exactly."*

**That is true on identical hardware and false across a heterogeneous fleet** — which is exactly the situation the desktop tier is. Different GPUs, drivers, kernels, thread counts, and quantisation paths change floating-point reduction order; when two logits are close, argmax flips; over hundreds of tokens, two *honest* nodes diverge.

Had we built on exact cross-node matching, the desktop trust model would have generated constant false accusations against honest volunteers.

**The reframe survives intact — it just rests on different mechanisms:**

| Mechanism | Works without determinism? |
|---|---|
| Canary tasks (known answers) | **Yes.** The primary control. |
| Coordinator re-derivation audits | **Yes.** Compares against a trusted reference, not between untrusted peers. |
| Numeric tolerance on `sci.*` and `infer.embed`/`classify`/`extract` | **Yes.** Numeric outputs compare within tolerance on any hardware. |
| Diversity constraints on assignment | **Yes.** Unaffected. |
| Exact match between two arbitrary nodes | **No.** Scoped to hardware cohorts only. |

Note the third row: **scientific task types verify better than chat.** Numeric kernels produce directly comparable outputs, so the tier with the weakest attestation happens to run the workload with the strongest verification. That is a convenient accident and it is worth leaning on.

Full mechanics in [threat-model.md §2](threat-model.md#2-verification-how-we-know-the-work-is-real).

---

## Threat 1 — poisoned results

An attacker who controls enough of a job's redundancy set can make all copies agree on a wrong answer. This is an **eclipse attack**, and it's the genuine danger on an unattested tier.

### Diversity constraints on node selection

Redundant copies of a job are never assigned to nodes that share:

- the same `/24` subnet or IPv6 `/48`
- the same autonomous system (ASN)
- the same rough geographic region
- the same reputation cohort or join-date window

A VM farm fails all four at once. Getting three colluding nodes onto one job requires genuinely distributed infrastructure across multiple providers and regions — expensive, slow, and noisy.

### Unpredictable assignment

Nodes cannot choose, request, or predict which jobs they receive. Targeting a specific request becomes impossible; an attacker can only hope to be selected, which diversity constraints already make unlikely.

### Coordinator re-derivation

For any result, the coordinator can silently re-run the job itself or on a high-reputation node. Cheap for small models and used as a random audit — so an attacker never knows which of their answers is being checked. **This is a primary control, not a backstop**, precisely because peer-to-peer exact comparison isn't available.

### Canaries, weighted toward new nodes

Jobs with known-correct answers, indistinguishable from real work. New and unattested nodes get a higher canary rate. Failing one forfeits accrued standing and triggers review of that node's recent output. Every task type in [the catalogue](task-types.md) must ship with a way to construct canaries — it's an acceptance criterion.

### Escalating redundancy

Low-stakes chat: 2 nodes. Research batch work: 3 or more, plus spot re-derivation. High-value scientific jobs: full replication with results published for independent checking.

---

## Threat 2 — prompt harvesting

A desktop operator can read what their machine processes. Same limitation as mobile, but easier to industrialise at scale on desktop.

Mitigations are structural rather than cryptographic:

- **No requester identity ever reaches a node.** No address, no account, no session token.
- **No session continuity.** Consecutive turns of a conversation are deliberately routed to different nodes, so no operator sees a whole thread.
- **Nodes cannot select workloads.** An attacker can't position themselves to catch particular traffic.
- **Sensitive tiers exist.** Users can opt into attested-only routing, accepting slower service for a smaller, hardware-verified node pool.
- **Volunteers can opt out of open request-serving** and take only vetted research batch jobs — which also removes them from this threat as an operator.
- **This limitation is disclosed on the website**, not buried in a repo document.

---

## Partial attestation is still available

"No attestation on desktop" is too pessimistic. A meaningful fraction of machines can prove something:

| Platform | Available root of trust |
|---|---|
| Windows 11 | TPM 2.0 remote attestation — mandatory hardware on every Win11 machine |
| macOS | App Attest via the Secure Enclave on Apple Silicon |
| Linux | TPM 2.0 where present; measured boot on some configurations |
| Everything else | None — treated as fully untrusted |

This produces a **trust ladder**, not a binary:

| Tier | Trust | What it may do |
|---|---|---|
| Mobile, attested | Highest | Any work, including single-node serving |
| Desktop, TPM / Secure Enclave attested | High | Single-node serving after reputation is established |
| Desktop, unattested | Low | Redundant work only, permanently. Higher canary rate. |
| Unattested + anomalous | None | Served nothing; results discarded |

Unattested nodes are never *excluded* — that would throw away most of the fleet's capacity, and the machines most likely to lack a TPM are older ones owned by exactly the people this project exists for. They're simply never trusted alone.

---

## Behavioural fingerprinting

Real hardware has a signature. Detection runs continuously:

- **Timing distributions.** A given model on a given GPU produces a characteristic tokens-per-second curve with characteristic variance. Emulated or shared hardware doesn't match it, and claimed capability that doesn't match measured throughput is an immediate flag.
- **Correlated lifecycle.** Nodes that appear, disappear, and idle in lockstep are one operator wearing many hats. Graph analysis over join times, uptime patterns, and subnets surfaces clusters cheaply.
- **Capability honesty checks.** A node claiming a 24GB GPU is periodically handed a job that genuinely requires one. Failure is disqualifying.
- **Impossible concurrency.** A thousand nodes on one physical machine cannot all return fast results simultaneously. Aggregate throughput per subnet is bounded by physics, and violations are visible.

This is also where the [availability-weighted credit design](economy.md#credit-for-availability-not-horsepower) helps: because credits accrue for *hours contributed* rather than throughput, a fake fleet gains nothing from claiming fast hardware — it would have to actually stay online and actually pass canaries.

---

## Slow trust, permanently

New desktop nodes start at zero and gain standing over weeks of verified work. An attacker must behave honestly at real compute cost for a long time before gaining any ability to misbehave — and the moment they defect, canaries and re-derivation catch it and reset them to zero.

This is deliberately unfair to legitimate newcomers. It is the correct trade for a tier that cannot prove what it is.

---

## What this does not fix

- **A well-resourced adversary with genuinely distributed infrastructure** — real machines across many providers, regions, and ASNs, behaving honestly for months — can eventually earn enough standing to poison some results. Redundancy and re-derivation limit the blast radius; they don't make it impossible. No open network solves this.
- **Desktop operators can read what they process.** Unfixable without TEEs. Say so plainly.
- **Behavioural fingerprinting is an arms race.** Detection improves, evasion improves. Treat it as raising cost, never as a solved problem.
- **Exact cross-node verification is unavailable** on mixed hardware, which is why canaries and re-derivation carry the load. If bit-exactness turns out to hold within some driver and GPU combinations, those become cohorts and verification gets cheaper — a bonus, not a plan.
- **None of this is audited yet.** Everything here is intent until an outside party has tried to break it.

---

## Sequencing

| Phase | Desktop security work |
|---|---|
| **M0** | Signed builds. Reproducibility measured across machines to find out where exact comparison is valid — a fast path, not a dependency. |
| **M1** | Diversity constraints on assignment; redundant execution; coordinator re-derivation audits; cohort detection. |
| **M2** | TPM and App Attest integration; trust ladder; canary weighting by tier; timing fingerprints. |
| **M3** | Published desktop threat model; external audit; attested-only routing option for users. |
