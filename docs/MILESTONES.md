# Milestones and issue-ready tasks

Each item below is written to be pasted directly into a GitHub issue. Titles are the issue titles; the body under each is the issue body.

Labels used: `M0` `M1` `M2` `M3` `M4` · `android` `coordinator` `protocol` `docs` `analysis` `security` `measurement` `good-first-issue` `help-wanted` · `blocker` `open-question`

---

## M0 — One node lives

**Goal:** prove the atomic unit works, and **replace the modelled performance figures in the whitepaper with measured ones.**

The second half is the one that matters. If the measurements contradict the model, the model changes and [WHITEPAPER.md](../WHITEPAPER.md) gets revised.

---

### #1 Run a 3B GGUF model on Android via llama.cpp
`M0` `android` `blocker`

Build a minimal Android app that loads a Q4_K_M GGUF model and streams tokens locally. No networking, no UI polish — just proof the runtime works on a real phone.

**Acceptance:**
- Loads a 1.5B and a 3B Q4_K_M model on a physical device
- Streams tokens to a text view
- Reports decode tok/s and prefill tok/s
- Documents the JNI build (NDK version, ABI, flags) so someone else can reproduce it

**Notes:** llama.cpp has an Android example to start from. Benchmark MLC-LLM against it before committing — [ARCHITECTURE.md §3.2](../ARCHITECTURE.md#32-inference-runtime) treats this as an open comparison, not a settled choice.

---

### #2 Implement the contribution gate
`M0` `android` `blocker`

All conditions from [ARCHITECTURE.md §3.3](../ARCHITECTURE.md#33-the-contribution-gate), evaluated continuously, failing closed.

**Acceptance:**
- Power connected, unmetered network, screen off, battery ≥80%, thermal nominal, user switch on
- Metered Wi-Fi hotspots correctly treated as ineligible
- Gate state change aborts in-flight work within 2 seconds
- One switch disables contribution with no confirmation dialog
- Unit tests for every condition and the conjunction

**Critical:** the gate is client-side and MUST NOT be remotely configurable. See the protocol invariant in [protocol-spec.md §5.3](protocol-spec.md#53-nodegate).

---

### #3 Foreground service with persistent notification
`M0` `android`

Contribution runs in a foreground service. The notification is always visible while active and states plainly what the device is doing.

**Acceptance:** survives Doze; notification cannot be dismissed while active; tapping it opens the contribution log.

---

### #4 Overnight measurement harness
`M0` `android` `measurement` `blocker`

**The most important issue in M0.** Instrument an 8-hour run and record everything needed to validate or refute the compute model.

**Acceptance — record at 1-minute intervals:**
- Decode tok/s (sustained, not burst)
- Battery level, temperature, and charge current
- Thermal throttling status
- Estimated power draw (watts)
- Interruption events with causes

**Deliverable:** a CSV per run plus a markdown summary with the device name attached, committed to `measurements/`.

**We publish these including if they are bad.** See the [energy honesty commitment](threat-model.md#energy-cost-and-honesty).

---

### #5 Minimal coordinator: registry
`M0` `coordinator`

Node.js + TypeScript. Accept `node.register`, `node.capability`, `node.gate`, `node.heartbeat` per [protocol-spec.md](protocol-spec.md). In-memory store is fine.

**Acceptance:** node connects and appears in a list; heartbeat timeout marks it offline; model SHA-256 served in `node.registered`.

---

### #6 Coordinator sends a prompt, node answers
`M0` `coordinator` `android`

The M0 demo: `work.assign` → `work.accept` → `work.progress` → `work.result`.

**Acceptance:** a prompt typed on a PC is answered by a phone on a charger across the room, streaming.

---

### #7 Publish the measured device table
`M0` `docs` `measurement` `analysis`

Take #4's output across as many device models as we can get and publish a table of measured tok/s, watts, and thermals with device names.

**Acceptance:**
- `measurements/DEVICES.md` with a row per device
- `analysis/compute_model.py` constants updated from measurements
- If figures moved materially, [WHITEPAPER.md](../WHITEPAPER.md) revised and the change noted in [Appendix B](../WHITEPAPER.md#appendix-b-what-we-retract)

---

### #8 `help-wanted`: benchmark your phone
`M0` `measurement` `help-wanted` `good-first-issue`

We need measured throughput across many device models and cannot build that table alone. Instructions once #4 lands.

---

## M1 — The network answers

**Goal:** prove routing and verification work between strangers' devices.

---

### #9 Capability-aware router
`M1` `coordinator`

Match work to nodes by measured throughput, current load, region, and reputation. Reassign on timeout.

---

### #10 Streaming relay
`M1` `coordinator`

Relay `work.progress` from node to requester. Instrument bytes relayed per token — this feeds the [bandwidth cost model](../WHITEPAPER.md#101-the-cost-structure), which is the cost that grows with success.

---

### #11 Redundant execution and semantic comparison
`M1` `coordinator` `open-question`

Send a sampled fraction to 2–3 nodes and compare.

**Blocked on an open question:** the agreement-scoring function is unspecified ([protocol-spec.md §7](protocol-spec.md#7-verification)). Needs a decision, and whatever is chosen must be published and independently computable.

**Acceptance:** sampling rate configurable and reported to nodes; disagreements logged and escalated; the scoring function documented and versioned.

---

### #12 Reputation scoring
`M1` `coordinator` `security`

Per [protocol-spec.md §8](protocol-spec.md#8-reputation). Slow accrual through verified work only.

**Open question:** how much of the function to publish without making it trivially gameable.

---

### #13 Live node map dashboard
`M1` `coordinator`

React + Vite. Nodes online, requests/min, tokens served, availability by region.

Also the recruiting asset — build it early. Use the protan-safe palette from [`analysis/compute_model.py`](../analysis/compute_model.py); no red as a signal colour.

---

### #14 Device attestation
`M1` `android` `security`

Play Integrity where available, affecting reputation ceiling and rate limits. **Non-attested nodes must still participate** — sideloaded and F-Droid builds cannot be excluded.

---

### #15 Alpha test with 10–50 volunteers
`M1` `help-wanted`

Recruit from r/LocalLLaMA, BOINC and Folding@home communities, and veteran/tech networks. Collect availability telemetry to test the [§6 model](../WHITEPAPER.md#6-follow-the-moon).

---

### #16 App store policy review
`M1` `blocker` `open-question`

Engage Play Store policy review *before* a public listing. Compute sharing is the stated purpose, disclosed, opt-in, foreground service.

**This is a genuine project risk** ([threat model](threat-model.md#app-store-removal)). Keep sideload + F-Droid as fallback.

---

## M2 — Follow the moon

**Goal:** prove the time-zone thesis with measured data, and run real science.

---

### #17 Region-aware routing
`M2` `coordinator`

Prefer night-side regions — that is where capacity is, and where nodes are least likely to be interrupted mid-request.

---

### #18 Publish the measured 24-hour availability curve
`M2` `measurement` `analysis`

M2's headline deliverable. Real telemetry from real nodes, published **against** the modelled curve in [§6](../WHITEPAPER.md#6-follow-the-moon), with the differences discussed rather than smoothed over.

**Acceptance:** measured mean, minimum, and maximum availability; model constants updated; whitepaper revised.

---

### #19 Batch job framework with checkpointing
`M2` `coordinator`

Small, idempotent, resumable work units. Phones are interrupted constantly — see [ARCHITECTURE.md §6](../ARCHITECTURE.md#6-batch-job-framework).

---

### #20 First real science batch job
`M2` `help-wanted`

Partner with an open-science project. Target shape: embarrassingly parallel, numerically verifiable, tolerant of interruption.

---

### #21 Schedule batch work against the availability curve
`M2` `coordinator`

Science fills the peak, throttles at the trough, leaves the ~14% floor free for interactive work.

---

### #22 libp2p peer discovery
`M2` `protocol`

Begin removing the coordinator from the data path. Economically load-bearing, not cosmetic.

---

### #23 iOS node
`M2` `open-question`

App-open-and-charging only. Decide whether it's worth the maintenance burden at all — see [ARCHITECTURE.md §10](../ARCHITECTURE.md#10-unresolved).

---

### #24 Publish energy cost per participant
`M2` `measurement` `docs`

Measured watt-hours per night and cost at typical residential rates. Committed to in the [threat model](threat-model.md#energy-cost-and-honesty).

---

## M3 — Open protocol

**Goal:** prove it outlives its founder.

---

### #25 Protocol specification v1.0
`M3` `protocol` `blocker`

Resolve every [open question in protocol-spec.md §11](protocol-spec.md#11-open-questions-before-v10) and publish a stable spec.

**This is the project's falsifiable commitment.** If it hasn't shipped by end of M3, the "centralised scaffolding" defence was a rationalisation. See [governance.md](governance.md#open-protocol-specification).

---

### #26 Third-party node interoperability test
`M3` `protocol`

Someone outside the project builds a compatible node from the spec alone, without asking us anything. That's the test.

---

### #27 Resolve the content-routing question
`M3` `security` `open-question` `blocker`

Decide and publish: Option B permanently, or Option C with a full safety design and legal review. See [threat model](threat-model.md#content-liability).

**The most consequential open decision in the design.**

---

### #28 Federated fine-tuning pilot
`M3` `security`

Behind every safeguard in [threat model → model poisoning](threat-model.md#model-poisoning). Highest-risk component; ships last for that reason.

---

### #29 Legal structure and constitution
`M3` `docs` `blocker`

Non-profit/foundation holding trademark and domain; constitution per [governance.md](governance.md#a-published-constitution) in force.

---

### #30 First institutional research partnership
`M3` `help-wanted` `blocker`

The funding model is unvalidated until this exists. See [WHITEPAPER.md §10.3](../WHITEPAPER.md#103-the-honest-gap).

---

## M4 — Public utility

### #31 Full P2P discovery, coordinator optional
`M4` `protocol`

### #32 Standing institutional research programme
`M4`

### #33 Multiple maintainers with release access
`M4` `blocker`

Until this exists, the founder is a single point of failure — stated plainly in [governance.md](governance.md#what-happens-if-the-founder-disappears).

---

## Cross-cutting: pinned issues

### #34 Check our math
`analysis` `help-wanted` `good-first-issue`

Standing invitation. [`analysis/compute_model.py`](../analysis/compute_model.py) generates every number we publish. Assumptions are named constants with confidence stated.

Weakest inputs, flagged by us:
- `THERMAL_DERATE` (0.70) — sustained vs burst over 8h
- `fp32_sustained_fraction` (0.30–0.33) — barely documented anywhere
- `SHARE_RAM_8GB_PLUS` (0.26) — hard to source precisely
- `DC_TOKENS_PER_SEC_PER_GPU` (3000) — wide real-world range

Finding an error here is the most valuable contribution available.

### #35 Open questions register
`open-question`

Living index of everything unresolved: [ARCHITECTURE.md §10](../ARCHITECTURE.md#10-unresolved), [protocol-spec.md §11](protocol-spec.md#11-open-questions-before-v10), [threat model residual risks](threat-model.md).
