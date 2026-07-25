# The task-type catalogue

**Layer 0: a job is a prompt plus a task-type ID. Never a script, never a binary, never a container.**

This document is the consequence of that rule, and its cost.

Because the network cannot execute submitted code, every kind of work it can do must be **implemented in the client, audited, and shipped in a signed release.** The set of things the network can compute is therefore a finite, versioned, public catalogue — this one.

That is a real product limitation, not a formality. It is written down here so nobody discovers it by surprise.

---

## Why the constraint exists

[THREAT_MODEL.md](threat-model.md#the-core-design-decision) makes the argument in full. In short: competing networks run general-purpose runtimes — Node.js, WASM, containers — because flexibility is useful. That flexibility *is* the attack surface. Refusing arbitrary code eliminates crypto mining, password cracking, malware, lateral movement, and proxy abuse **structurally rather than by policy.**

A volunteer running Meridian Moonlight does not have to trust our intentions, our vetting process, or our sandbox. There is no execution path for those attacks to use.

We consider that trade permanent, and it applies to **every tier** — phones and desktops alike. There is no privileged tier that runs submitted code.

---

## What that costs

Stated plainly:

- **A researcher cannot bring a novel simulation.** If the work they need isn't in the catalogue, they wait for a release.
- **New task types move at the speed of client releases and audits**, which is weeks to months, not hours.
- **Some science is permanently out of reach**, because implementing it as a fixed kernel isn't practical.
- **We are the bottleneck**, and that is an uncomfortable amount of power over what the network is used for. The [governance process](#requesting-a-new-task-type) below exists to constrain it.

This directly limits the "earn your compute instead of buying it" promise in [ECONOMY.md](economy.md#spending). A researcher can earn credits and spend them submitting *data* against an existing task type. They cannot spend credits submitting *code*.

---

## The catalogue

**Status: nothing below is implemented.** This is the planned catalogue with target milestones. `v0` types are the ones M0–M2 will actually ship.

### Inference types

These are the native shape of the network and carry the mobile tier.

| ID | Version | What it does | Tier | Verification |
|---|---|---|---|---|
| `infer.chat` | v0 | Interactive conversation, streamed | all | Cohort exact-match / semantic |
| `infer.complete` | v0 | Single-shot completion, no history | all | Cohort exact-match / semantic |
| `infer.embed` | v0 | Text → embedding vector | all | **Numeric, exact within tolerance** |
| `infer.classify` | v0 | Text → label from a supplied set | all | Exact — discrete output |
| `infer.extract` | v0 | Text → structured fields per a supplied schema | all | Exact — discrete output |
| `infer.summarise` | v0 | Long text → summary | all | Semantic |
| `infer.translate` | v1 | Text → target language | all | Semantic |

Note how much easier the last four are to verify than open-ended chat. `classify`, `extract`, and `embed` produce outputs that can be compared **exactly or within numeric tolerance across heterogeneous hardware** — which is precisely the problem that makes chat verification hard. Batch inference is both the better commercial product and the easier one to police.

### Scientific types

These carry the desktop tier. Each is a fixed numeric kernel with a defined input schema.

| ID | Version | What it does | Tier | Verification |
|---|---|---|---|---|
| `sci.dock.score` | v1 | Score a ligand pose against a receptor grid | desktop | Numeric tolerance + replication |
| `sci.embed.corpus` | v1 | Bulk embedding of a document set | all | Numeric tolerance |
| `sci.md.replica` | v2 | Fixed-integrator MD trajectory replica, checkpointed | desktop (dGPU) | Numeric tolerance + replication |
| `sci.ensemble.param` | v2 | Parameter-sweep member of a supplied ensemble model | desktop | Numeric tolerance |
| `sci.signal.scan` | v2 | Matched-filter scan over a time-series segment | desktop | Numeric tolerance |

**Scientific task types verify better than chat, not worse.** Numeric outputs are directly comparable within a stated tolerance, which sidesteps the whole determinism problem described in [ARCHITECTURE.md](../ARCHITECTURE.md#5-verification). This is a genuine advantage of the science workload, and it is why the desktop tier's trust model is more tractable than the mobile tier's despite having weaker attestation.

### Explicitly excluded, permanently

| Not supported | Why |
|---|---|
| Submitted source code, scripts, or bytecode | Layer 0 |
| Containers or VM images | Layer 0 |
| WASM modules, even sandboxed | Layer 0. A sandbox escape would be catastrophic and unrecoverable for trust |
| Arbitrary network access from a job | No job may open a socket |
| Arbitrary filesystem access | Jobs receive their input as data and return output as data |
| Model training or fine-tuning on a node | Separate mechanism, [federated updates](../ARCHITECTURE.md#7-federated-improvement-m3), M3+ |
| Anything whose output cannot be verified | If we cannot check it, we cannot pay credits for it |

That last row is a useful filter. A proposed task type that produces unverifiable output is not merely risky — it is unusable, because [credits require verified work](economy.md#earning).

---

## Requesting a new task type

The process is public, and the fact that we are the bottleneck is why it has to be.

1. **Open an issue** using the task-type template. State the scientific or product purpose, the input and output schema, the expected per-unit runtime, and — critically — **how a result can be verified.**
2. **Public discussion.** Minimum 14 days. Anyone may object.
3. **Security review** against the criteria below, published in the issue.
4. **Reference implementation** with test vectors, including canary cases with known answers.
5. **Ships in a signed client release.** Participants are told what new work their device may now accept, and [re-confirm consent](threat-model.md#1-protecting-volunteers) when a release changes the accepted work types.
6. **Catalogue and this document updated**, with the version it landed in.

### Acceptance criteria

A proposed task type must satisfy **all** of these:

- **Bounded.** Fixed maximum runtime, memory, and output size per unit. No unbounded loops.
- **Pure.** No network, no filesystem, no clock dependence, no source of nondeterminism beyond documented floating-point variation.
- **Verifiable.** A concrete comparison method with a stated tolerance, plus a way to construct canaries.
- **Interruptible.** Safe to kill mid-execution; either cheap to restart or checkpointed.
- **Auditable.** Implementation is readable by a non-specialist reviewer in reasonable time.
- **Useful to more than one submitter.** We are not shipping a release for a single lab's bespoke need.

### What gets rejected

Requests that amount to "please add a general-purpose runtime," anything whose output cannot be checked, and anything whose safety depends on trusting the submitter rather than on the shape of the work.

---

## Versioning

Task types are versioned independently of the client. A node advertises which `(type, version)` pairs it supports; the coordinator never sends work a node hasn't declared.

Deprecation gets one release of overlap minimum. Removing a task type that institutions depend on is announced with a timeline, because someone's research schedule is attached to it.

---

## The honest summary

This catalogue is the price of the security promise, and it is a price worth stating clearly rather than discovering later:

**The network can only ever compute things we have already implemented.** That makes it far safer than a general-purpose volunteer compute network, meaningfully less capable, and dependent on a governance process to stay legitimate.

If that trade is wrong, the argument to make is in [the issues](../../issues/new) — but it should be made against [THREAT_MODEL.md's reasoning](threat-model.md#the-core-design-decision), not against this catalogue, because the catalogue is only a consequence.
