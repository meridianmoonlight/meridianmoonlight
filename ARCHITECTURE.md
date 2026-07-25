# Architecture

Technical design, and the reasoning behind each decision. Where a choice is contested or unresolved, it says so.

Companion documents: [WHITEPAPER.md](WHITEPAPER.md) for the quantitative argument, [docs/threat-model.md](docs/threat-model.md) for adversarial analysis, [docs/protocol-spec.md](docs/protocol-spec.md) for wire formats.

---

## 1. Design principles

1. **Layer 0 - no arbitrary code, ever.** A job is a prompt plus a task-type ID from a compiled-in allowlist. Never a script, binary, container, or WASM module. On every tier. This is the constraint the rest of the security model is built on, and it is not relaxable.
2. **Local-first.** The default path for a request is the requester's own device. The network is the fallback.
3. **Whole models only.** No model is ever split across the network.
4. **Fail closed.** Any ambiguity in the contribution gate resolves to *not contributing*.
5. **Centralised scaffolding, decentralised building.** Ship a working thing, then remove the centre.
6. **Measure, then claim.** Every performance figure in this project is either measured or explicitly labelled as modelled.

---

## 2. System shape

```
                       ┌─────────────────────────┐
                       │      COORDINATOR        │
                       │  registry · router ·    │
                       │  verifier · scheduler   │
                       └──────────┬──────────────┘
                                  │  control plane (WebSocket, JSON)
              ┌───────────────────┼───────────────────┐
              │                   │                   │
       ┌──────▼──────┐     ┌──────▼──────┐     ┌──────▼──────┐
       │  NODE       │     │  NODE       │     │  NODE       │
       │ Android     │     │ Android     │     │ Desktop     │
       │ ┌─────────┐ │     │ ┌─────────┐ │     │ ┌─────────┐ │
       │ │llama.cpp│ │     │ │llama.cpp│ │     │ │llama.cpp│ │
       │ │ 3B Q4   │ │     │ │ 3B Q4   │ │     │ │ 8B Q4   │ │
       │ └─────────┘ │     │ └─────────┘ │     │ └─────────┘ │
       │  gate ✓     │     │  gate ✓     │     │  gate ✓     │
       └─────────────┘     └─────────────┘     └─────────────┘
              ▲
              │ local inference — never leaves the device
       ┌──────┴──────┐
       │    USER     │
       └─────────────┘
```

From M2, the data plane moves peer-to-peer (libp2p) and the coordinator brokers connections instead of relaying content. That change is [economically load-bearing](WHITEPAPER.md#10-economics-who-pays), not cosmetic — relay bandwidth is the cost that grows with success.

---

## 3. The node

### 3.1 Two tiers, built in parallel

**Mobile is the mission. Desktop is the research instrument.** Both clients are M0 work, because neither blocks the other and they answer different questions.

| | Mobile | Desktop |
|---|---|---|
| Carries | Scale, reach, the reason the project exists | 85% of scientific capacity |
| Model hosted | 1.5B-3B Q4 | 3B-8B Q4 |
| Gate | Charging + Wi-Fi + screen off + >=80% + cool | Powered + unmetered + idle |
| Availability | 25.7% mean | 19.6% mean - people switch PCs off |
| Attestation | Play Integrity / DeviceCheck | TPM 2.0 / App Attest, or none |
| Blockers to shipping | App-store review, background limits, thermals | None of those |

Android permits a foreground service with a persistent notification - exactly the right primitive: the work is visible by construction and the OS won't kill it mid-request.

**Desktop reaches a working demo faster** because it has no app-store gate, no background-execution limit, and no thermal ceiling. It also hosts larger models, which makes it useful as a reference node for [verification](#5-verification). Its weaker attestation story is handled in [docs/desktop-security.md](docs/desktop-security.md).

iOS is deferred and will be a weaker participant. Background execution limits effectively forbid sustained compute; an iOS node can realistically only contribute while the app is open and charging. We plan for that rather than pretending parity.

### 3.2 Inference runtime

**llama.cpp** via JNI. Rationale: mature mobile support, GGUF quantisation, active development, permissive licence, and a working Android example to start from. MLC-LLM is the main alternative and is worth benchmarking against in M0 rather than dismissing.

Model per device tier — the router must treat these as *different capabilities*, not interchangeable capacity:

| Device RAM | Model | Weights (Q4) | Role |
|---|---|---|---|
| ≥8GB | 3B-class | ~1.80 GB | Full node |
| 6GB | 1.5B-class | ~0.95 GB | Light node |
| <6GB | none | — | Requester only |
| Desktop | 8B+ | ~4.5 GB+ | Reference / verification node |

Weights must be openly licensed with terms that survive planetary scale. Some widely used "open" licences carry monthly-active-user thresholds and acceptable-use terms that bind downstream distributors. Prefer Apache-2.0 or MIT. Any community-licensed model must have its terms reviewed against projected scale *before* adoption, and the review published. See [WHITEPAPER.md §3.6](WHITEPAPER.md#36-model-selection-and-licensing).

### 3.3 The contribution gate

All conditions must hold. Evaluated continuously, not once at start. Fails closed.

| Condition | Threshold | Why |
|---|---|---|
| Power connected | AC or USB | Battery life is what users notice first and forgive last |
| Network | Wi-Fi (unmetered) | Never spend a participant's cellular data |
| Screen | Off | Never compete with the user for their own device |
| Battery level | ≥ 80% | Don't slow the charge they actually wanted |
| Battery temperature | Below platform-nominal | Stop before the user ever feels warmth |
| User switch | On | Always visible; off is immediate and permanent |

Implementation notes: `BatteryManager` for power and level, `ConnectivityManager.isActiveNetworkMetered` for the Wi-Fi test (metered Wi-Fi hotspots must count as cellular), `PowerManager.isInteractive` for screen state, and a thermal check via `PowerManager.getCurrentThermalStatus`. Any gate condition failing mid-request aborts the request and returns it to the coordinator for rerouting — a partially served request is discarded, never returned as a result.

**Withdrawal must be trivially easy.** One switch in the main view, no confirmation dialog that argues, no retention flow. Uninstalling is a complete exit with no residue.

### 3.4 Capability reporting

On registration and periodically, a node reports: RAM class, SoC identifier, hosted model, measured tokens/sec from a local benchmark, current thermal headroom, and gate state. Measured throughput — not a datasheet figure — is what the router schedules against.

This reporting is also the project's measurement instrument. The aggregate becomes the published device table that replaces the modelled figures in the whitepaper.

---

## 4. The coordinator

Node.js + TypeScript. Chosen for iteration speed, not for throughput; if it becomes the bottleneck, that is a good problem and a rewrite in Go is a known path.

Four responsibilities:

**Registry.** Node identity, capability, reputation, liveness. Nodes are ephemeral and interruption is the normal case, not an error.

**Router.** Matches work to nodes by capability, current load, region (night-side preferred — that's where capacity is *and* where nodes are least likely to be interrupted), and reputation.

**Verifier.** Redundant execution on a sampled fraction of work. See §5.

**Scheduler.** Batch jobs queued against the availability curve: science work fills the peak and throttles at the trough, leaving the ~14% floor free for interactive requests.

### 4.1 On being centralised

This is the most obvious criticism of the design and the honest answer is: yes, for now, deliberately.

Peer discovery is a hard problem that adds nothing to proving the core idea works, and every functioning decentralised system bootstrapped through a centralised phase. The plan: libp2p peer discovery begins in M2; the protocol is specified in M3 so a third party can run their own coordinator without asking.

**The commitment is falsifiable: if the protocol spec hasn't shipped by the end of M3, this criticism was correct and we failed.**

---

## 5. Verification

Language model output is **not bit-deterministic across heterogeneous hardware.** Different SoCs, GPUs, drivers, kernels, thread counts, and quantisation paths change floating-point reduction order; when two logits are close, argmax flips; over hundreds of tokens two *honest* nodes diverge. An earlier draft of this project built verification on cross-node exact match, which would have generated false accusations against honest volunteers.

Four mechanisms, in order of the weight they carry:

1. **Canary tasks - primary.** Known-answer jobs, indistinguishable from real work, higher rate for new and unattested nodes. Every task type must ship with a way to build them.
2. **Coordinator re-derivation - primary.** Silent random audits, re-running work on the coordinator or a high-reputation reference node. Compares untrusted output against a *trusted* reference, so heterogeneity is irrelevant.
3. **Cohort-scoped exact match.** Nodes grouped by SoC/GPU, build, and thread configuration; inside a cohort exact comparison is valid and free. How coarse a cohort can be is measured in M0.
4. **Semantic tolerance across cohorts.** A published, versioned similarity threshold. Must be independently computable or third-party coordinators cannot interoperate.

**Numeric task types verify best.** Scientific kernels, embeddings, classification, and extraction produce outputs comparable exactly or within a stated tolerance on *any* hardware. Open-ended chat is the hardest case, not the easiest - which is why the desktop tier's trust model is tractable despite weaker attestation.

Sampling rate is a cost dial: verification at 3× redundancy costs 3× the compute. We sample rather than verify everything, and **we publish the sampling rate** — an unpublished rate is indistinguishable from no verification.

Reputation inputs: uptime, latency, completion rate, agreement rate. New nodes start at zero and earn trust through sustained verified work, which is also the main brake on Sybil attacks ([threat model](docs/threat-model.md#sybil-resistance)).

Deliberately unsophisticated. It needs no cryptographic novelty, works from the first version, and produces the reputation signal everything else depends on. Verifiable computation schemes (ZK proofs of inference) are research-grade and orders of magnitude too expensive; revisit if that changes.

---

## 6. Batch job framework

Science work is latency-insensitive by construction, which is what makes it a good fit for hardware that vanishes without warning.

**Constrained by Layer 0:** a batch job selects an audited [task type](docs/task-types.md) and supplies data and parameters. It never supplies code. A researcher whose work is not in the catalogue must request a new task type and wait for a signed release - a real product limitation, documented in the catalogue and in [WHITEPAPER 3.5](WHITEPAPER.md#35-layer-0-and-the-task-type-catalogue).

Requirements this imposes:

- **Checkpointing is mandatory.** A phone is interrupted constantly — the user picks it up, unplugs it, or it gets warm. Work units must be small enough to complete inside a typical uninterrupted window, or resumable from a checkpoint. Long molecular-dynamics trajectories need ensembles of independent replicas rather than single long runs.
- **Idempotent work units.** Any unit may be executed more than once, by design (verification) and by accident (interruption plus retry).
- **Result verification.** Same redundant-execution approach, but scientific outputs are often numerically comparable, which makes verification cheaper and stronger than it is for text.
- **Workload vetting.** Under the recommended [content policy](docs/threat-model.md#content-liability), only identified institutions with reviewed workloads may submit batch work. This is a governance gate, not a technical one.

---

## 7. Federated improvement (M3+)

Federated fine-tuning: devices compute updates on local usage patterns, only aggregated gradients leave the device, and no personal data moves.

This is the highest-risk component in the design and ships last for that reason. Any participant contributing gradients can attempt to steer the model. Mitigations — robust aggregation discarding outliers, update clipping, holdout evaluation gates before promotion, staged rollout with automatic rollback — are described in the [threat model](docs/threat-model.md#model-poisoning).

Do not ship this before the verification and reputation systems have real operating history.

---

## 8. Privacy architecture

What **never** leaves a device: prompts, conversations, personal data, local model state.

What **does** cross the network: node capability reports, routing metadata, batch job inputs and outputs, verification comparisons, and from M3 aggregated model updates.

Metadata is not nothing. Request timing and volume leak information; the coordinator sees which node served what. Therefore: minimise retention, publish the log schema and retention period as a public interface, and treat changes to it as requiring the same scrutiny as a protocol change.

---

## 9. Technology choices, with the reasoning

| Layer | Choice | Why | Alternative considered |
|---|---|---|---|
| On-device inference | llama.cpp | Mature mobile support, GGUF, permissive licence | MLC-LLM — benchmark against it in M0 |
| Mobile platform | Kotlin / Android | Foreground service + charging detection are actually permitted | iOS — background limits forbid it; deferred |
| Coordinator | Node.js + TypeScript | Iteration speed | Go — the rewrite path if throughput demands it |
| Control plane | JSON over WebSocket | Simple, debuggable, adequate | protobuf — from M2 |
| Data plane | Coordinator relay → libp2p (M2) | Removes the cost that grows with success | Permanent relay — economically unviable |
| Verification | Redundant execution + reputation | Works day one, no novel cryptography | ZK proofs of inference — research-grade, far too expensive |
| Dashboard | React + Vite | Static hosting, no build complexity | — |
| Figures & model | Python + matplotlib | One auditable script, reproducible by anyone | Spreadsheet — not auditable |

---

## 10. Unresolved

Listed because pretending these are settled would be the actual architectural flaw.

1. **Semantic agreement thresholds.** What similarity score constitutes "agreement" for text output is unsolved, probably needs to be empirical and per-model, and must end up published and independently computable.
2. **Cohort granularity.** How coarse a hardware cohort can be before exact comparison produces false positives. M0 measures it.
3. **Sybil resistance without stake or a trusted registry.** We bound the damage rather than solving it. Nobody has solved it without one of those two things, and we've ruled out stake.
4. **Battery health over years.** No longitudinal data exists and won't for a year. Currently an assumption, and a load-bearing one for trust.
5. **iOS viability at all.** It may turn out that an iOS node is too weak to be worth the maintenance burden.
6. **How the task-type catalogue stays legitimate.** Layer 0 makes the maintainers the arbiters of what the network can do. The public request process constrains that imperfectly.
7. **Ride Acurast's protocol, or build the stack?** They have 250k+ nodes and a working TEE-based network. Owning the consumer layer and the mission on top of someone else's compute layer is a live option and not yet decided.
