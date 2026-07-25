# Protocol specification

**Status: DRAFT v0.1 — design sketch, not a stable interface. Nothing implements this yet.**

This document becomes the open standard that lets third parties build compatible nodes and run competing coordinators. That is an M3 deliverable and [the project's falsifiable commitment against the centralisation criticism](governance.md#open-protocol-specification).

Until v1.0 it will change without notice.

---

## 1. Scope

Covers the **control plane**: how a node registers, reports capability, receives work, returns results, and is verified.

Explicitly *not* covered yet:

- Peer-to-peer discovery and transport (M2 — libp2p)
- Federated update aggregation (M3)
- Batch job submission by institutions (M2 — will be a separate document)

## 2. Design constraints

1. **Nodes are ephemeral.** Disconnection is the normal case, not an error. Every message must be safe to lose.
2. **Nodes are untrusted.** Every claim a node makes about itself is unverified until corroborated.
3. **Work is idempotent.** Any unit may execute more than once — by design (verification) and by accident (interruption + retry).
4. **The coordinator is replaceable.** No message may depend on coordinator-private state that a third-party implementation couldn't reproduce.
5. **Debuggable before fast.** JSON over WebSocket through M1; protobuf from M2.

## 3. Transport

- **M0–M1:** JSON over a single WebSocket per node, TLS required. Node-initiated.
- **M2+:** protobuf over libp2p streams; the coordinator brokers connections rather than relaying payloads.

Heartbeat every 30 s. Three missed heartbeats marks the node offline and reassigns its outstanding work.

## 4. Message envelope

Every message:

```json
{
  "v": 1,
  "id": "01J8XK2QRSTUVWXYZ0123456789",
  "type": "node.register",
  "ts": "2026-07-25T02:14:03.221Z",
  "payload": { }
}
```

| Field | Type | Notes |
|---|---|---|
| `v` | int | Protocol major version. Mismatch → connection refused with `error.version` |
| `id` | string | ULID. Unique per message; used for correlation and replay rejection |
| `type` | string | `namespace.action` |
| `ts` | string | RFC 3339, UTC, millisecond precision |
| `payload` | object | Type-specific |

Responses carry `re` set to the originating `id`.

## 5. Node lifecycle

```
   node.register  ──────────────►
                  ◄────────────── node.registered
   node.capability ─────────────►
   node.gate ───────────────────►        (whenever gate state changes)
                  ◄────────────── work.assign
   work.accept ─────────────────►
   work.progress ───────────────►        (optional, streaming)
   work.result ─────────────────►
                  ◄────────────── work.ack
   node.heartbeat ──────────────►        (every 30s)
```

### 5.1 `node.register`

```json
{
  "node_key": "ed25519:BASE64URL",
  "client": { "name": "meridian-android", "version": "0.1.0" },
  "attestation": { "kind": "play_integrity", "token": "..." }
}
```

`node_key` is a device-generated Ed25519 public key, persistent across restarts, and the node's identity. All subsequent messages are signed with it.

`attestation` is optional but affects reputation ceiling and rate limits. Absence is permitted — sideloaded and F-Droid builds must be able to participate — but attested nodes are preferred in verification quorums. See [Sybil resistance](threat-model.md#sybil-attacks).

**Response `node.registered`:**

```json
{
  "node_id": "nd_01J8XK...",
  "reputation": 0.0,
  "assigned_model": { "id": "qwen2.5-1.5b-instruct-q4_k_m",
                      "sha256": "...", "url": "https://..." },
  "policy": { "heartbeat_s": 30, "max_concurrent": 1,
              "verification_sample_rate": 0.15 }
}
```

`verification_sample_rate` is sent to the node deliberately: [the sampling rate is published](../ARCHITECTURE.md#5-verification), because an unpublished rate is indistinguishable from no verification.

**The node MUST verify `sha256` before loading any model and refuse on mismatch.** This is the primary defence against [coordinator compromise](threat-model.md#coordinator-compromise).

### 5.2 `node.capability`

```json
{
  "ram_mb": 8192,
  "soc": "sm8650",
  "os": { "name": "android", "api": 34 },
  "model_id": "qwen2.5-1.5b-instruct-q4_k_m",
  "benchmark": {
    "tokens_per_sec_decode": 14.2,
    "tokens_per_sec_prefill": 210.0,
    "measured_at": "2026-07-25T02:10:00Z",
    "thermal_status_during": "none"
  },
  "fp32_gflops": 268.0
}
```

`benchmark` is **measured locally, not a datasheet figure**. The router schedules against measured throughput. These reports are also the project's measurement instrument — the aggregate becomes the published device table that replaces the modelled figures in the [whitepaper](../WHITEPAPER.md#52-cross-checking-against-reality).

### 5.3 `node.gate`

```json
{
  "eligible": false,
  "conditions": {
    "power_connected": true,
    "network_unmetered": true,
    "screen_off": false,
    "battery_pct": 91,
    "thermal_status": "none",
    "user_enabled": true
  }
}
```

Sent on every state change. `eligible` is the node's own conjunction of all conditions.

**The coordinator MUST NOT assign work to a node reporting `eligible: false`, and MUST NOT ever instruct a node to override its own gate.** The gate is enforced client-side and is not remotely configurable. This is a hard protocol invariant: a coordinator that violates it is non-compliant, and a node implementation that honours such an instruction is non-compliant.

## 6. Work

### 6.1 `work.assign`

```json
{
  "work_id": "wk_01J8XK...",
  "task_type": "infer.chat",
  "task_version": 0,
  "deadline": "2026-07-25T02:15:00Z",
  "payload": {
    "prompt": "...",
    "max_tokens": 512,
    "temperature": 0.7,
    "seed": 42
  },
  "stream": true
}
```

**`task_type` is the Layer 0 boundary.** It names an entry in [the audited catalogue](task-types.md) that is implemented *in the client*. There is no field anywhere in this protocol that carries code, bytecode, a container reference, or a URL to fetch executable content from — and adding one would be a breaking change to the security model, not just to the schema.

**A node MUST reject any `task_type` it has not declared support for in `node.capability`, and MUST reject any `task_type` absent from the allowlist compiled into its own build.** A compromised coordinator therefore cannot introduce new work types; see [threat-model.md](threat-model.md#coordinator-compromise).

`seed` is included for reproducibility where it is meaningful. Identical seeds do **not** produce identical output across different SoCs, kernels, thread counts, or quantisation paths, so seed equality is not a verification mechanism on its own. See §7.

### 6.2 `work.accept` / `work.reject`

A node MAY reject with `busy`, `gate_ineligible`, `model_mismatch`, `payload_too_large`, or `deadline_infeasible`. Rejection is not penalised — an honest rejection is more useful than a timeout.

### 6.3 `work.progress`

```json
{ "work_id": "wk_01J8XK...", "delta": "The mitochond", "tokens_out": 3 }
```

### 6.4 `work.result`

```json
{
  "work_id": "wk_01J8XK...",
  "status": "complete",
  "output": "...",
  "metrics": {
    "tokens_out": 412,
    "duration_ms": 29400,
    "tokens_per_sec": 14.0,
    "thermal_status_end": "light",
    "interrupted": false
  },
  "sig": "ed25519:BASE64URL"
}
```

`status` is `complete`, `aborted_gate`, `aborted_deadline`, or `error`.

**`aborted_gate` results MUST be discarded, never returned to a requester.** A partially served request is not a result. The work is reassigned.

`sig` covers the canonical serialisation of `work_id` + `output` + `metrics`, signed with the node key. It provides attribution, not proof of correct execution — a node can sign a wrong answer. Correctness comes from §7.

## 7. Verification

Language model output is **not bit-deterministic across heterogeneous hardware.** Different SoCs, kernels, thread counts, and quantisation paths change floating-point reduction order; when two logits are close, argmax flips; over hundreds of tokens two *honest* nodes diverge. Verification therefore cannot be built on cross-node exact comparison.

Four mechanisms, in order of how much weight they carry:

**1. Canary tasks — primary.** Jobs with known-correct answers, indistinguishable from real work. Every task type in [the catalogue](task-types.md) must ship with a way to construct them. Nodes are never told which jobs are canaries. New and unattested nodes receive a higher rate.

**2. Coordinator re-derivation — primary.** The coordinator silently re-runs a sampled fraction on itself or a high-reputation reference node. Compares untrusted output against a *trusted* reference rather than between two untrusted peers, so heterogeneity is irrelevant.

**3. Cohort-scoped exact match.** Nodes are grouped into cohorts by `soc`, `client.version`, and thread configuration, reported in `node.capability`. **Within** a cohort, bit-exact comparison is valid and free. The coordinator advertises cohort membership in `node.registered`.

**4. Semantic tolerance across cohorts.** A published, versioned similarity function with a stated threshold. The function and threshold **must** be published and independently computable, or third-party coordinators cannot interoperate — see §11.

### Verification by output kind

| Task-type family | Comparison | Strength |
|---|---|---|
| `sci.*` | Numeric, stated tolerance | **Strongest** — hardware-independent |
| `infer.embed` | Vector distance, stated tolerance | Strong |
| `infer.classify`, `infer.extract` | Exact — discrete output | Strong |
| `infer.summarise`, `infer.translate` | Semantic threshold | Moderate |
| `infer.chat` | Cohort exact, else semantic | **Weakest** |

Note the ordering: the scientific and batch workloads verify *better* than open-ended chat, because their outputs are numerically comparable on any hardware. This is why the desktop tier's trust model is tractable despite weaker attestation.

Disagreement escalates to a trusted reference node rather than immediately penalising either party. Persistent disagreement with an adjudicated result reduces reputation until exclusion.

## 8. Reputation

A single scalar in `[0, 1]`, starting at 0, accruing slowly through sustained verified work — it cannot be bought or rushed. Inputs: uptime, completion rate, latency consistency, verification agreement rate, attestation presence.

**The exact function is intentionally unspecified in v0.1.** Publishing it precisely invites gaming; keeping it secret forever is incompatible with an open protocol. The resolution — probably a published function with unpublished parameters, or a published function that is expensive to game — is unresolved and must be settled before v1.0.

## 9. Errors

```json
{ "code": "gate_ineligible", "message": "screen_off is false", "retry_after_s": 60 }
```

| Code | Meaning |
|---|---|
| `error.version` | Protocol major version mismatch |
| `error.auth` | Signature verification failed |
| `error.rate_limit` | Too many requests from this identity |
| `error.gate_ineligible` | Node not currently eligible |
| `error.model_mismatch` | Node does not host the required model |
| `error.payload` | Malformed or oversized |
| `error.internal` | Coordinator fault; retry with backoff |

## 10. Versioning

`v` is the major version. Breaking changes increment it; the coordinator supports at least the two most recent majors for a minimum of 90 days. Additive fields are non-breaking, and unknown fields MUST be ignored.

## 11. Open questions before v1.0

1. **Semantic agreement scoring** — the function and threshold for cross-cohort comparison (§7). Must end up published and independently computable.
2. **Cohort definition** — how coarse can a hardware cohort be before exact match starts producing false positives? M0 measures this.
3. **Reputation function disclosure** — how open without being gameable (§8).
4. **Requester–node unlinkability** — the mechanism that makes [prompt harvesting](desktop-security.md#threat-2--prompt-harvesting) structurally hard, including how session turns are split across nodes.
5. **Batch job submission** — how an institution submits data against a catalogue task type. Separate document, M2.
6. **P2P transport** — libp2p stream multiplexing, NAT traversal, M2.
7. **Attestation on unattested platforms** — sideloaded, F-Droid, and no-TPM desktop builds must participate without being second-class beyond the reputation ceiling ([trust ladder](desktop-security.md#partial-attestation-is-still-available)).

Comments on any of these: [open an issue](../../issues/new).
