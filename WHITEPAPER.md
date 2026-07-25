# Meridian Moonlight

## A free AI network built from the world's sleeping phones

**Version 0.1 — July 2026**
**Status: proposal. Nothing in this document has been built yet.**

---

## Abstract

Capable AI runs almost entirely inside data centres owned by a handful of companies. Meanwhile roughly 1.2 billion smartphones with enough memory to host a modern small language model sit on chargers every night, doing nothing.

Meridian Moonlight proposes to use them. Each participating phone runs a *complete* small model locally — never a fragment — and contributes spare capacity only while charging, on Wi-Fi, and idle. Because night circles the planet continuously, the supply of contributed compute migrates westward around the clock and never falls to zero.

This document is unusual in one respect: **its central quantitative claim is a downward revision of an earlier draft of this same project.** That draft asserted that ~30 million devices (1.4% of the capable fleet) would surpass the largest AI data centre on Earth. That claim was built on peak NPU throughput figures and does not survive a bandwidth-bound analysis. The honest figure is roughly 12 billion devices — more smartphones than exist. **The network will not out-compute a hyperscale data centre in raw operations, and no amount of adoption changes that.**

What survives is stronger, because it does not depend on winning a compute race:

1. **The network is self-sufficient at every scale.** Capacity and membership grow together, so each participant's share of capacity is roughly 274,000 output tokens per day — about **9× more than heavy personal use**, and 5× even at the daily supply trough. This ratio is identical at one thousand devices and at one billion. There is no threshold to cross before the network is useful to the people in it.
2. **The surplus is a research instrument.** At roughly **31 million enrolled devices** the network continuously matches the peak throughput of Folding@home, the largest volunteer computing effort in history. At full enrolment of today's capable fleet it delivers about **92 exaFLOPS sustained, ~38× Folding@home's peak**, indefinitely.
3. **Its structural advantages are ones data centres cannot copy** — marginal cost near zero, hardware already paid for, no single point of control, and privacy-preserving federated analysis over data that legally cannot be centralised.

Every number above is produced by [`analysis/compute_model.py`](analysis/compute_model.py), which is a few hundred lines of commented Python that anyone can run, audit, and disagree with. The assumptions are named constants. The sensitivity of every conclusion to every assumption is published in [§7](#7-sensitivity-what-if-we-are-wrong). We would rather be corrected than believed.

---

## Contents

- [1. The problem](#1-the-problem)
- [2. What physics forbids](#2-what-physics-forbids)
- [3. Architecture](#3-architecture)
- [4. The fleet](#4-the-fleet)
- [5. The bandwidth wall](#5-the-bandwidth-wall)
- [6. Follow the moon](#6-follow-the-moon)
- [7. Sensitivity: what if we are wrong](#7-sensitivity-what-if-we-are-wrong)
- [8. What the network is for](#8-what-the-network-is-for)
- [9. Threat model](#9-threat-model)
- [10. Economics: who pays](#10-economics-who-pays)
- [11. Governance](#11-governance)
- [12. Prior art and positioning](#12-prior-art-and-positioning)
- [13. Roadmap](#13-roadmap)
- [14. How to falsify this](#14-how-to-falsify-this)
- [Appendix A: derivations](#appendix-a-derivations)
- [Appendix B: what we retract](#appendix-b-what-we-retract)

---

## 1. The problem

Three problems compound as AI becomes more consequential.

**Access is gated.** Capable AI costs money, requires a reliable connection to a distant server, and can be priced out, rate-limited, geo-blocked, or switched off. The people least able to pay are the people for whom a competent tutor, translator, or medical-information assistant would matter most.

**Capability follows capital.** Whoever owns the compute owns the capability. Individuals and communities are consumers of intelligence and never owners of it. Independent researchers and universities increasingly cannot afford to run the experiments they can design.

**The infrastructure is concentrated.** Data centres are enormous, expensive, energy-hungry, and few. That makes them efficient, and it also makes them chokepoints — commercially, politically, and during disasters.

There is an asymmetry worth sitting with. The most widely distributed computing hardware ever manufactured is already in people's pockets, already paid for, already plugged in every night. Its idle capacity is currently worth exactly nothing to anyone.

### 1.1 An honest tension in the mission

The framing "free AI for the three billion people excluded from paid AI" contains a problem we should name rather than paper over: **the people most excluded from paid AI largely do not own the phones that can run these models.** An 8GB-RAM handset is not a poverty device.

So the mission has to be stated in two parts:

- **Contributors** are disproportionately in wealthier markets, because that is where capable hardware is.
- **Beneficiaries** need not be. A network node serves whoever asks, and a 2GB phone that cannot host a model can still hold a conversation with one.

That asymmetry is not a flaw. It is the entire point: it is a transfer of capability from people who have spare silicon to people who do not. But describing it as "giving three billion people a phone that runs AI" would be false, and we do not say it.

---

## 2. What physics forbids

Credibility in this space is established by what you rule out. Three limits are not engineering challenges to be overcome — they are properties of the problem.

### 2.1 This is not one giant brain

Splitting a single large model across phones connected by the internet does not work, and the reason is worth being precise about.

Generating one token requires activations to pass sequentially through every layer of the model. If layers live on different devices, each token costs a network round trip per layer boundary. Inside a data centre, chip-to-chip interconnects deliver hundreds of gigabytes per second at sub-microsecond latency. Between two phones on consumer internet, you have tens of milliseconds and single-digit megabytes per second. That is a gap of five to six orders of magnitude, in the one dimension the workload is most sensitive to.

A 28-layer model split across 28 phones with 40 ms hops spends over a second of pure network latency per token. This is not a matter of better software.

**Meridian does not fight this. Every node runs a complete model.** The network layer routes, verifies, and aggregates; it never carries activations mid-forward-pass.

### 2.2 This will not train frontier models

Training synchronises gradients across the entire parameter set every step. That requires memory bandwidth between processors measured in terabytes per second, which requires the processors to be physically adjacent. Wide-area networks are not a substitute, and no protocol design changes this.

Federated *fine-tuning* of an already-trained small model is a different and genuinely tractable problem, because updates are sparse, compressible, and tolerant of staleness. That is in scope. Pre-training is not.

### 2.3 The compute is throughput, not a pooled engine

A million phones can run a million independent tasks. They cannot make one task a million times faster.

The right mental image is a million couriers, not one cargo jet. Couriers are superb at delivering a million parcels to a million addresses and useless for moving a single shipping container. Every workload described in [§8](#8-what-the-network-is-for) decomposes into independent pieces. Workloads that do not decompose are out of scope, permanently.

### 2.4 And one limit that is not physics, but is real

**Data centres batch. Phones cannot.**

This is the single most important asymmetry in the document, and it is why [§5](#5-the-bandwidth-wall) reaches the conclusion it does. When a data centre serves a language model, it processes hundreds of user requests concurrently against one copy of the weights. Each weight is read from memory once and used hundreds of times. The expensive resource — memory bandwidth — is amortised across every concurrent user.

A phone serving one user has a batch size of one. Every weight is read from memory, used once, and discarded. The phone pays the full bandwidth cost per token that the data centre spreads across hundreds of tokens.

Per unit of hardware, a data centre is therefore *dramatically* more efficient at inference than a phone — by roughly the batch factor. Any honest proposal in this space has to concede that up front. Meridian's advantages lie elsewhere: the hardware is already bought, the electricity is already being spent, and the marginal cost of the next token is zero.

---

## 3. Architecture

### 3.1 Local-first, network-second

The default path for a user's request is the user's own device. No network, no coordinator, no third party, no latency beyond the phone in their hand.

The network exists for three cases:

1. The requesting device cannot host a model at all (under 6GB RAM).
2. The requesting device is busy, hot, or on battery.
3. The request is a batch job rather than a conversation.

This ordering is not an optimisation. It is the privacy architecture, the cost architecture, and — as [§9.2](#92-the-hard-problem-whose-content-runs-on-whose-phone) argues — most of the safety architecture. Every request served locally is a request that generates no bandwidth bill, no log, and no liability.

### 3.2 The contribution gate

A device contributes only when **all** of the following hold:

| Condition | Why |
|---|---|
| Plugged into power | Battery life is the thing users notice first and forgive last |
| On Wi-Fi | Never spend a participant's cellular data |
| Screen off and idle | Never compete with the user for their own device |
| Battery above 80% | Do not slow the charge the user actually wanted |
| Device temperature nominal | Stop before the user ever feels warmth |

The gate is enforced in the client, checked continuously, and fails closed. Withdrawal is immediate and needs no explanation: one switch, always visible, and uninstalling is a complete exit.

We publish our own thermal and battery measurements from the M0 overnight runs, including any bad results. A project asking for space on someone's personal device does not get to be selective about its data.

### 3.3 Routing and verification

A coordinator matches requests to nodes by capability, current load, geography, and reputation.

Verification is by **redundant execution**: a sampled fraction of requests goes to two or three independent nodes and the results are compared. Language model output is not bit-deterministic across devices, so comparison is semantic rather than exact — agreement is scored on distributional similarity above a threshold, with disagreements escalated to a trusted reference node.

This is deliberately unsophisticated. It requires no cryptographic novelty, works from day one, and produces the reputation signal that makes everything else tractable. Nodes accrue reputation from uptime, latency, and agreement rate; low-reputation nodes get verified more often and are eventually excluded.

Verified compute is expensive — redundant execution at a 3× rate costs 3× the compute. We spend it on a sampled fraction, not on everything, and we publish the sampling rate.

### 3.4 Centralised scaffolding, decentralised building

Phases M0–M1 use a single central coordinator. This is a deliberate choice, and we would rather be criticised for it honestly than pretend otherwise.

Every functioning decentralised system bootstrapped through a centralised phase, because peer discovery is a hard problem that adds nothing to the proof that the core idea works. The coordinator is replaced by libp2p-based peer discovery starting in M2, and the protocol is specified so that a third party can run their own coordinator by M3.

The commitment is testable: **if the protocol spec has not shipped by the end of M3, this criticism is correct and we have failed.**

### 3.5 Model selection and licensing

Model weights must be openly licensed, and the licence must survive planetary scale. This is a real constraint, not a formality: several widely used "open" model licences carry monthly-active-user thresholds above which separate permission is required, plus acceptable-use terms that bind downstream distributors. A network that intends to reach hundreds of millions of users cannot adopt weights whose licence quietly caps it.

Our position: **prefer Apache-2.0 or MIT weights.** Where a Llama-family or other community-licensed model is technically preferable, its terms must be reviewed against the network's projected scale *before* adoption, and the review published. Verifying the licence status of every candidate model is tracked work, not an assumption.

---

## 4. The fleet

The binding constraint on whether a phone can be a node is RAM. Model weights, KV cache, and the operating system must coexist without the app being evicted — Android will kill a background process long before it swaps.

| Quantity | Value |
|---|---|
| Active smartphones worldwide | ~4.6 billion |
| Share with ≥8GB RAM | ~26% |
| **Capable fleet, today** | **~1.2 billion devices** |
| Capable fleet, 2030 projection | ~2.4 billion devices |

An earlier draft of this project used 2.2 billion as the *present-day* capable fleet. That is a plausible figure for around 2030 and roughly double the truth today: 8GB became common in the mid-tier only recently, and the installed base lags shipments by a three-to-four-year replacement cycle. All "today" claims in this document use 1.2 billion.

Devices are modelled in three classes, because a fleet average that ignores the mid-tier flatters itself:

| Class | Share | Usable bandwidth | Model hosted | Sustained tok/s | Sustained FP32 |
|---|---|---|---|---|---|
| Flagship (LPDDR5X) | 30% | 42.2 GB/s | 3B Q4 | 16.4 | 450 GFLOPS |
| Upper-mid (LPDDR5) | 45% | 25.5 GB/s | 3B Q4 | 9.9 | 280 GFLOPS |
| Mid (LPDDR4X) | 25% | 16.0 GB/s | 1.5B Q4 | 11.8 | 150 GFLOPS |
| **Fleet-weighted** | 100% | — | — | **12.3** | **299 GFLOPS** |

The mid tier posts a *higher* token rate than the upper-mid tier because it hosts a smaller model. Those tokens are not equivalent in quality — this is a capability/throughput trade, and the router must treat the two tiers as serving different purposes rather than as interchangeable capacity.

---

## 5. The bandwidth wall

This section contains the project's most important technical claim, and it is a negative one.

### 5.1 Why peak TOPS is the wrong number

A current flagship phone advertises roughly 45 INT8 TOPS of neural accelerator throughput. It is tempting to multiply that by a billion devices and announce a very large number. Doing so is wrong by more than two orders of magnitude, and it is the error the previous draft of this project made.

Autoregressive decoding at batch size 1 is bound by memory bandwidth, not arithmetic. To generate one token, every weight in the model must be read from DRAM into the accelerator. The ceiling is therefore:

```
tokens/second  =  usable memory bandwidth (GB/s)  ÷  weight footprint (GB)
```

For a 3B-parameter model at Q4 quantisation — about 1.80 GB including scales and the higher-precision tensors quantisation schemes retain — on a flagship with roughly 42 GB/s of *achievable* bandwidth:

```
42.2 GB/s ÷ 1.80 GB  =  23.4 tokens/second
```

At two operations per parameter per token, that is 141 GOPS — **0.141 TOPS against an advertised 45.** Applying a sustained-operation derate of 0.70 for an eight-hour overnight run on a charging, warming device gives **0.098 TOPS**.

**The gap between the marketing figure and the figure that actually serves a user is roughly 457×.**

![The bandwidth wall](docs/figures/fig1_bandwidth_wall.png)

The chip is not slow. It is starved. Its arithmetic units spend most of their cycles waiting for weights to arrive.

### 5.2 Cross-checking against reality

A model that disagrees with measurements is worthless, so: published llama.cpp results for 3B-class models at 4-bit quantisation on recent Snapdragon and Dimensity flagships generally land in the mid-teens to mid-twenties of tokens per second for burst decode. Our modelled 23.4 tok/s burst sits inside that band, toward the optimistic end.

This is the weakest link in the model, and it is deliberately the *first* thing the roadmap fixes. Milestone 0 exists to replace these modelled figures with measurements from real devices under real thermal conditions, published as a table with the device names attached.

### 5.3 The claim we retract

Running the corrected figures through to the comparison the earlier draft made:

| Comparison | Enrolled devices needed |
|---|---|
| Match Folding@home's peak, sustained | **31 million** |
| Match a 100k-GPU cluster's *serving throughput* | ~95 million |
| Match a 100k-GPU cluster's *peak INT8 operations* | **~12 billion — not reachable** |

Twelve billion devices exceeds every smartphone in existence by a factor of two and a half. The "1.4% adoption beats the largest data centre" claim is dead, and no reformulation rescues it.

We could have quietly dropped it. Publishing the retraction instead is the point: a project whose headline number was revised downward by its own authors, with the arithmetic shown, is one whose remaining numbers are worth reading.

### 5.4 What replaces it: self-sufficiency

Here is the reframing, and it is a better thesis than the one it replaces.

The network does not need to beat a data centre. It needs to serve the people in it. And it does that **from the first thousand devices**, because capacity and membership grow together:

| | Value |
|---|---|
| Capacity per participant, 24-hour mean | **274,000 output tokens/day** |
| Capacity per participant, at the daily trough | 151,000 output tokens/day |
| Heavy individual use | ~30,000 output tokens/day |
| **Headroom** | **9.1× mean, 5.0× worst case** |

![Supply and demand grow together](docs/figures/fig2_self_sufficiency.png)

The three lines on that chart are parallel. That is the whole argument. There is no adoption threshold to cross, no critical mass to reach, no chicken-and-egg problem to solve with token incentives. A thousand-device network is useful to its thousand members in exactly the proportion that a billion-device network is useful to its billion.

Note how conservative the demand line is: it assumes *every* participant is a heavy daily user. Real usage distributions are long-tailed, so actual headroom will be considerably larger.

**The surplus above member use is what goes to science.** At 9× headroom, roughly 89% of network capacity is available for research work without any participant noticing a degraded experience.

---

## 6. Follow the moon

Demand for an assistant peaks during waking hours. Supply of idle charging phones peaks overnight. Naively that looks like a fatal mismatch, and on a single continent it would be.

The planet solves it. Night is not a global state; it is a band that circles the Earth continuously. When it is 2 p.m. in New York it is 2 a.m. in Shanghai, where the largest concentration of capable handsets on Earth is sitting on chargers.

### 6.1 Modelling availability honestly

The previous draft assumed 95% overnight availability. That implicitly assumes every enrolled user charges every night, on Wi-Fi, undisturbed. People do not behave that way. We model the conjunction:

| Component | Value |
|---|---|
| Charges overnight on a given night | 72% |
| On home Wi-Fi rather than cellular-only | 86% |
| Undisturbed through the window | 97% |
| **Overnight peak (joint)** | **60.1%** |
| Daytime baseline (desk/car charging that meets the gate) | 5% |

We also drop the step-function bedtime. People go to bed at different times, and a phone plugged in at 21:00 is contributing well before midnight, so the overnight window is modelled as a smooth curve over the local clock centred on 02:00.

Geography is modelled as a continuous density across inhabited longitudes rather than as a handful of point clusters. This matters: four point clusters produce a moment when all four happen to be in daylight, creating an artificial global trough that is a modelling artefact rather than a fact about Earth.

### 6.2 The result

![Follow the moon](docs/figures/fig3_follow_the_moon.png)

| Quantity | Value |
|---|---|
| Global mean availability | 25.7% |
| Global maximum (Asian night) | 40.8% |
| **Global minimum (the floor)** | **14.1%** |

The floor is the important number. Availability oscillates by a factor of about three across the day, but **it never falls below roughly 14% of the enrolled fleet.** Somewhere on Earth it is always 3 a.m., and the network is always being fed.

Two consequences for the design:

- **Region-aware routing is worth building.** Requests should prefer the night-side region, both because that is where capacity is and because those nodes are least likely to be interrupted mid-request.
- **Batch work should be scheduled against the curve.** Science jobs are latency-insensitive by construction, so they belong in the peak and can be throttled at the trough, leaving the floor free for interactive requests.

The curve above is modelled. Publishing the *measured* 24-hour curve from real nodes is Milestone 2's headline deliverable, and it will differ from this one.

---

## 7. Sensitivity: what if we are wrong

Publishing a model without publishing its fragility is a marketing exercise. Below: each key assumption varied across a plausible range, and its effect on the load-bearing scientific claim — the enrolment needed to match Folding@home's peak.

![Sensitivity](docs/figures/fig6_sensitivity.png)

| Assumption varied | Low | High |
|---|---|---|
| Sustained FP32 fraction (0.5× / 2×) | 16M | 63M |
| Folding@home's peak, exaFLOPS (1.2 / 4.8) | 16M | 63M |
| Share who charge overnight (0.50 / 0.90) | 26M | 43M |
| Device mix (low-end skew / flagship skew) | 26M | 41M |
| **Baseline** | **31M** | |

The full range across every assumption is roughly 16 million to 63 million devices — a factor of four. For a claim about hardware that has not been benchmarked yet, spanning a global fleet, a 4× band is a defensible degree of confidence, and it is small enough that the conclusion does not change character anywhere inside it.

The two widest sensitivities are both worth naming:

- **Sustained FP32 fraction** is our least certain input. Mobile GPU sustained floating-point throughput over multi-hour runs is barely documented, because nobody runs mobile GPUs that way. M0 measures it.
- **Folding@home's peak** is a reported figure, not an audited one, and mixes precisions. We use 2.4 exaFLOPS and show what happens at half and double.

---

## 8. What the network is for

### 8.1 At any scale: a private assistant that costs nothing

From the first device: chat, translation, summarisation, and question-answering running locally on hardware the participant already owns, with no account, no subscription, no request leaving the device, and no rate limit but the phone's own speed.

For the substantial population whose device cannot host a model, the network answers instead. This is the transfer described in [§1.1](#11-an-honest-tension-in-the-mission).

Let us be clear about quality: a 3B model is not a frontier model. It is genuinely useful for translation, summarisation, drafting, explanation, and tutoring, and it is genuinely worse than a paid frontier model at hard reasoning. The offer is "capable, private, and free," not "as good as the best."

### 8.2 At ~31M devices and beyond: a research instrument

![Scientific batch capacity](docs/figures/fig4_science_capacity.png)

| Enrolled devices | Sustained FP32 | vs Folding@home peak |
|---|---|---|
| 1 million | 0.08 exaFLOPS | 0.03× |
| 10 million | 0.77 exaFLOPS | 0.32× |
| **31 million** | **2.4 exaFLOPS** | **1.0×** |
| 100 million | 7.7 exaFLOPS | 3.2× |
| 1.2 billion (full capable fleet) | **92 exaFLOPS** | **38×** |

At full enrolment, roughly **ten days** of the network delivers what Folding@home delivered in a year at its COVID-era peak — the largest volunteer computing effort in history, which produced real published results on viral protein dynamics.

That is a genuine claim, and it is roughly 30× smaller than the previous draft's version of it. Both figures are large. Only one is defensible.

What that instrument suits, in rough order of confidence:

**Virtual screening for drug discovery.** Embarrassingly parallel by construction — each compound-target pair is independent. Screening campaigns are currently sized to budgets rather than to chemistry. The strongest version of this argument concerns rare and neglected diseases, which go uninvestigated precisely because screening cost cannot be justified against a small patient population. Near-zero marginal compute changes that calculation.

**Materials and catalyst search.** Battery chemistries, carbon-capture catalysts, photovoltaic compounds. Systematic search across candidate space, again independent per candidate.

**Molecular dynamics.** Structure prediction is largely solved; *dynamics* — how proteins move, misfold, and interact over time — is not, and it is compute-hungry. Long-timescale misfolding simulations relevant to Alzheimer's, Parkinson's, and ALS are currently rationed. Note the caveat: MD needs long trajectories, which suits ensembles of independent replicas better than single long runs, and phones are interrupted often. This requires careful checkpointing to be useful at all.

**Climate ensembles.** Projections carry wide uncertainty bands partly because large ensembles are expensive. Researchers run tens of variations where thousands would be scientifically preferable.

**Astronomy and signal search.** Radio survey analysis, transient and fast-radio-burst searches, gravitational-wave candidate sifting. This is volunteer computing's original home, and it fits the shape exactly.

**Federated analysis over data that cannot be centralised.** This is the one no data centre can offer at any price. Models can learn across millions of consenting individuals' health or behavioural data without any record leaving any device. The blocker here is privacy law and data-sharing agreements, not compute scarcity — which means the architecture, not the scale, is the unlock.

### 8.3 And the boundary

Everything above decomposes into independent tasks. That is not a coincidence; it is a filter. Workloads requiring terabytes per second of inter-processor bandwidth — frontier pre-training above all — are permanently out of scope. Saying so is what makes the rest credible.

---

## 9. Threat model

### 9.1 Malicious and faulty nodes

**Garbage results.** Redundant execution with semantic comparison, plus reputation scoring, from the first version. A node that disagrees with consensus loses reputation and gets sampled more heavily.

**Sybil attacks.** Cheap identity creation lets an attacker manufacture reputation or dominate a verification quorum. Mitigations: device attestation where the platform provides it, reputation that accrues slowly with sustained real work, quorum selection weighted to reputation and diversified across network origin, and rate limits per attestation. We do not solve Sybil resistance completely — nobody has without either a trusted registry or a costly stake, and we have ruled out the latter. We bound the damage instead.

**Model poisoning via federated updates.** Any participant contributing gradients can attempt to steer the model. Mitigations: robust aggregation that discards outliers, update clipping, holdout evaluation gates before any aggregated update is promoted, and staged rollout with automatic rollback. Federated fine-tuning does not ship before M3 for this reason — it is the highest-risk component in the design.

**Extraction of model weights.** Weights are on the user's device, so they are extractable. We treat this as a non-issue by construction: only openly licensed weights are distributed, so there is nothing to steal.

### 9.2 The hard problem: whose content runs on whose phone

Routing a stranger's prompt to a volunteer's phone means **a stranger's content is processed on a private individual's hardware, in their home, under their jurisdiction.** Some fraction of arbitrary prompts will be illegal to process somewhere. This is the risk most likely to end the project, and any proposal that omits it should not be taken seriously.

We see three options.

**Option A — route third-party inference, with content filtering.** Maximum utility, and it puts an unbounded legal and moral liability on volunteers. A local classifier reduces incidence but cannot be relied upon, and the participant is still the one whose device did the processing.

**Option B — inference stays strictly local; the network carries only vetted batch work.** A participant's device runs a model *for its owner only*. The network's shared capacity is spent exclusively on batch jobs from identified, accountable institutions with reviewed workloads. Nobody's phone ever processes an anonymous stranger's prompt.

**Option C — Option B, plus an explicit opt-in tier** for participants who choose to serve third-party inference, with filtering, informed consent, and jurisdiction awareness.

**Our recommendation is Option B for M0 through M2, moving to Option C only with an explicit, published safety design.**

This is a real cost. It means the "free AI for people whose device can't run a model" promise is deferred — arguably the most emotionally compelling part of the pitch. We think that is the right trade: the project cannot ask volunteers to accept legal exposure they do not understand, and one bad incident in year one ends everything.

**This is the most consequential open decision in the design, and it is flagged as such rather than settled by default.**

### 9.3 Privacy

Personal data never leaves the device. What crosses the network is: node capability reports, routing metadata, batch job inputs and outputs, verification comparisons, and — from M3 — aggregated model updates.

Metadata is not nothing. Request timing and volume leak information about a participant, and the coordinator sees which node served what. We minimise retention, publish what is logged and for how long, and treat the coordinator's log schema as a public interface subject to review.

### 9.4 Platform and policy risk

**App store rejection.** Background compute contribution has been grounds for removal when it was *concealed* or bundled into an app that appeared to do something else. Our position: compute sharing is the app's entire stated purpose, disclosed in the store listing, opt-in at first run, and visible in a persistent notification while active. On Android this is a legitimate foreground service. This is a real risk and we may be wrong about it.

**iOS.** Background execution limits on iOS effectively forbid this model. An iOS node will be app-open-and-charging only, which makes it a far weaker participant. We plan for Android first and treat iOS as a partial capability rather than pretending parity.

**Energy honesty.** The network is not free of energy cost. Running a phone's SoC at load draws real watts, paid for by the participant, and "the phone was plugged in anyway" does not mean the electricity is free. We commit to measuring and publishing marginal watt-hours per participant per night, and marginal cost at typical residential rates, from M0 onward. If that number is embarrassing, publishing it is still the deal.

---

## 10. Economics: who pays

The promise is: free to join, free to use, no token, no ads, no sale of user data or user access. That promise requires knowing what actually costs money.

### 10.1 The cost structure

Notably, **compute is not a cost.** The hardware belongs to participants and the electricity is theirs. What costs money:

| Cost | Scales with | Notes |
|---|---|---|
| Coordinator hosting | Requests, sub-linearly | Small until millions of nodes |
| **Bandwidth / egress** | Requests routed through the coordinator | **The dominant cost, and the reason for local-first** |
| Model weight distribution | New installs × weight size | Mitigate with CDN, peer distribution, delta updates |
| Development and security | Fixed-ish | The real long-run cost |

Bandwidth deserves the arithmetic. Relayed tokens are roughly 4 bytes each. At 1 million enrolled devices with all traffic relayed, aggregate capacity of ~3.2M tok/s implies ~13 MB/s — trivial. At 100 million devices, ~317M tok/s implies ~1.3 GB/s sustained, or about 10 Gbps. That is a genuine infrastructure bill, and it is the cost that grows with *success*.

Two structural mitigations, both already in the architecture rather than bolted on:

1. **Local-first** means the overwhelming majority of interactive requests never touch the coordinator at all.
2. **Peer-to-peer transfer** from M2 removes the coordinator from the data path entirely; it brokers connections rather than relaying content.

Under Option B in [§9.2](#92-the-hard-problem-whose-content-runs-on-whose-phone), relayed inference traffic approaches zero by design, and the coordinator carries batch job payloads on a schedule we control.

### 10.2 Where money comes from

**Institutional batch compute partnerships.** Research bodies, universities, foundations, and nonprofits pay for access to overnight batch capacity — at rates far below cloud, because our marginal compute cost is zero. This is the intended primary funding line.

**Grants and philanthropy.** Open-science infrastructure and digital-inclusion funders are a natural fit for exactly this.

**Never:** selling participant access, participant data, participant attention, or a token.

### 10.3 The honest gap

**We do not yet have a validated funding model, and we should not pretend otherwise.** No institution has agreed to pay for anything. The first partnership is an M3 deliverable, which means M0–M2 must be affordable to run essentially unfunded — which is achievable precisely because at those scales the bandwidth bill is small.

A structural risk deserves naming: if institutional batch work becomes the revenue source, there will be pressure to prioritise paying workloads over participant experience. The governance model has to make that trade-off explicit and public rather than leaving it to whoever is running the coordinator.

### 10.4 Why we don't sell the compute and pay participants

This is the most frequent suggestion the project receives, and it deserves a costed answer rather than an appeal to principle. Full workings: [`analysis/ECONOMICS.md`](analysis/ECONOMICS.md), generated by [`analysis/participant_economics.py`](analysis/participant_economics.py).

**The magnitude settles it.** One phone contributes roughly 673 TFLOP-hours a year. Interruptible, unverified compute on consumer hardware does not fetch cloud rates, and after utilisation, verification overhead, and platform costs, about **$1.32 a year** reaches the participant. Their own electricity — around 9.3 kWh at the wall — costs more than that in most of the world:

| Market | Earnings | Electricity | **Net** |
|---|---|---|---|
| India ($0.08/kWh) | $1.32 | −$0.74 | **+$0.57** |
| United States ($0.17/kWh) | $1.32 | −$1.58 | **−$0.26** |
| United Kingdom ($0.29/kWh) | $1.32 | −$2.69 | **−$1.37** |
| Germany ($0.40/kWh) | $1.32 | −$3.71 | **−$2.40** |

![What a participant would earn](docs/figures/fig7_participant_earnings.png)

In most markets the participant would **pay to contribute**. A deliberately optimistic scenario — full cloud pricing, 80% utilisation, a 10% platform cut — reaches about **$8 a year**. That is roughly one hour of minimum wage, annually.

Payment rails finish the argument. At $1.32 a year, a monthly payout is eleven cents against a typical $0.28 transaction fee: **fees exceed the payment entirely.** The only rail that makes micropayments this small viable is a token, which is the one thing this project has committed never to issue — and the thing that has confined every competitor to the crypto niche ([§12](#12-prior-art-and-positioning)).

**The non-financial costs are worse than the numbers.** Payment would:

1. **Attach a cash bounty to our one unsolved security problem.** [Sybil resistance is bounded, not solved](docs/threat-model.md#sybil-attacks). Today a fake node earns nothing. Under payment, every fake node is revenue, and emulator farms are cheap.
2. **Make app-store approval harder.** Paying for background resource use moves the app into the category stores scrutinise most, and hands a reviewer an accurate description that sounds bad.
3. **Convert volunteers into paid contractors** — income reporting, worker-classification questions, advertised-earnings rules, cross-border tax. A compliance surface larger than the engineering surface, requiring real legal advice.
4. **Destroy the only unclaimed position.** It would make this the fifteenth token-adjacent compute marketplace, with less funding than the incumbents.
5. **Create a constituency lobbying to weaken the contribution gate** — hotter phones and longer windows mean more income. This directly contradicts [constitution item 7](docs/governance.md#a-published-constitution).
6. **Outbid science on its own network.** Corporate buyers will pay more than research bodies. The surplus is the reason the project exists.

**What the suggestion gets right.** Two things. The funding model genuinely is unvalidated ([§10.3](#103-the-honest-gap)), and there is a real fairness argument: if a corporation profits from work done on someone's hardware, that person's interest in the proceeds is not frivolous. The objection is not to the motive — it is that at this magnitude, cash cannot honour either concern.

**What we do instead.** Sell batch compute to institutions *including* corporations, but distribute it as a commons rather than as cash: hosting, development, and a published research grant pool, with **open books** — every dollar in and out published quarterly. Reciprocate to contributors in capability rather than currency (priority routing, larger models, higher quotas), which is real value with no payment rails, no tax status change, and no fraud incentive. And let participants direct their notional share to a research project of their choosing, which preserves the gift framing and turns the accounting into the point: *your phone funded this study.*

"Owned by no one, with open books" is a stronger claim than "earn sixty cents a year."

---

## 11. Governance

A network asking for space on a million personal devices owes them a say in it, and a project claiming to be "owned by no one" has to mean it structurally.

**Now (pre-M3):** benevolent-dictator, openly acknowledged. One author, public decisions, all discussion in public issues. Pretending otherwise at this size would be theatre.

**By M3, published and in force:**

- **Open protocol specification** so a third party can run a compatible node and a competing coordinator without permission.
- **Contributor governance** with an explicit path from contributor to maintainer to decision-maker.
- **A non-profit or foundation structure** holding the trademark and domain, so the project cannot be quietly sold.
- **A published constitution** covering: free-forever for individuals, no token, no advertising, no sale of user data, no dark-pattern consent, and a defined process for changing those commitments that is deliberately hard to invoke.
- **A right to fork that is real** — permissive licence, portable data, documented protocol. If the stewards go bad, the network should be able to leave them behind.

The success condition for M3 is stated in [§13](#13-roadmap) as "proof it outlives its founder." That is the actual test.

---

## 12. Prior art and positioning

Volunteer distributed computing is a solved and proven idea. SETI@home and Folding@home became household names and produced real science; BOINC still runs dozens of projects. What none of them did was serve interactive AI, and what none of them had was a device already in every pocket.

The recent decentralised-compute cohort — Acurast, Pocket Network, Destra, Exo Labs and others — is technically serious and has established that phone-based compute is not absurd. Nearly all of them pay contributors in cryptocurrency and resell the compute. That solves the cold-start problem with financial incentive, and it also caps the audience at people who want a crypto wallet. None has crossed into mainstream adoption.

Exo Labs deserves specific credit for demonstrating model-splitting across local devices over fast local links. That is a genuinely different problem from splitting across the internet, and [§2.1](#21-this-is-not-one-giant-brain) is not a criticism of it.

**The unclaimed position is the one SETI@home occupied:** ordinary people contributing to something worthwhile, for free, because it feels good and costs them nothing they notice. No wallet, no yield, no speculation. Just a checkbox and a mission.

The moat is not the protocol — the protocol is meant to be copied. The moat is trust, radical simplicity, and a mission normal people want to be part of. Which is also why the honesty in this document is not a stylistic choice: **trust is the entire competitive strategy,** and a project that inflates its numbers has spent the only asset it has.

---

## 13. Roadmap

![Roadmap](docs/figures/fig5_roadmap.png)

Every milestone ships something that runs.

### M0 — One node lives (month 0–1, 1 device)

Prove the atomic unit. An Android app runs a 3B GGUF model via llama.cpp, streams tokens locally, enforces the contribution gate, reports capability to a coordinator, and survives an eight-hour overnight run.

**Deliverable that matters most: measured tok/s, sustained watts, and thermals from real devices, published as a table — replacing the modelled figures in [§5](#5-the-bandwidth-wall).** If the measurements contradict the model, the model changes and this document is revised.

### M1 — The network answers (month 1–3, ~100 devices)

Routing between real volunteers' devices, streaming relay, redundant verification with semantic comparison, reputation scoring, and a live node map. Recruit 10–50 alpha testers.

*Demo: a question asked in Arizona, answered by a batch job on a volunteer's phone in another time zone.*

### M2 — Follow the moon (month 3–9, ~10K devices)

Region-aware routing, the **measured** 24-hour availability curve published against the model in [§6](#6-follow-the-moon), a batch job framework with checkpointing for interrupted work, the first real science batch job, initial libp2p peer discovery, and an iOS node within its constraints.

### M3 — Open protocol (month 9–18, ~100K devices)

Protocol specification v1.0 so third parties can build compatible nodes. Federated fine-tuning pilot behind the safeguards in [§9.1](#91-malicious-and-faulty-nodes). Governance structure in force per [§11](#11-governance). First institutional research partnership. Resolution of the [§9.2](#92-the-hard-problem-whose-content-runs-on-whose-phone) question with a published safety design.

*Success condition: proof it outlives its founder.*

### M4 — Public utility (month 18+, 1M+ devices)

Full peer-to-peer discovery, a standing institutional research programme, and a network that no single party can switch off.

---

## 14. How to falsify this

The claims in this document that could be shown wrong, and what would show it:

| Claim | How to falsify |
|---|---|
| Phones sustain ~12 tok/s fleet-weighted on a 3B Q4 model | Measure it. M0. If real devices manage 3 tok/s, the inference case weakens sharply |
| Mobile GPUs sustain ~300 GFLOPS FP32 over hours | Measure it. This is our least certain input and the science case rests on it |
| ~60% of enrolled devices are available overnight | Instrument it. M1–M2. Telemetry from real enrolled devices |
| Availability never falls below ~14% | Publish the measured 24-hour curve. M2 |
| Thermals and battery are unnoticeable | Publish overnight measurements including the bad ones. M0 |
| An 8-hour run does not degrade battery health | This needs longitudinal data we will not have for a year. Currently an assumption |
| App stores will permit this | Submit and find out. M1 |
| Institutions will pay for batch compute | Sign one. M3 |
| Volunteers will join without payment | Ship M1 and count |

If the M0 measurements come back badly enough, the right response is to say so publicly and revise the document — the same thing we did to the previous draft's central claim, which is how this version came to exist.

---

## Appendix A: derivations

Everything here is implemented in [`analysis/compute_model.py`](analysis/compute_model.py) and regenerated by running it. Full derived output: [`analysis/NUMBERS.md`](analysis/NUMBERS.md). Machine-readable: [`analysis/numbers.json`](analysis/numbers.json).

### A.1 Capable fleet

```
capable_fleet = install_base × share_ram_8gb_plus
              = 4.60e9 × 0.26
              = 1.20e9 devices
```

### A.2 Per-device decode throughput

For each device class:

```
usable_bandwidth  = peak_bandwidth × usable_fraction
tokens_per_sec    = usable_bandwidth ÷ weight_footprint      # batch size 1
sustained         = tokens_per_sec × thermal_derate          # 0.70, 8h run
ops_per_token     = 2 × parameters                           # one multiply, one add
sustained_ops     = sustained × ops_per_token
```

Flagship worked example:

```
42.2 GB/s ÷ 1.80 GB              = 23.4 tok/s burst
23.4 × 0.70                      = 16.4 tok/s sustained
16.4 × 2 × 3e9                   = 98.4 GOPS = 0.098 TOPS
45 TOPS ÷ 0.098 TOPS             = 457× gap vs the marketed figure
```

Fleet-weighted by class share: **12.3 tok/s, 65 GOPS INT8, 299 GFLOPS FP32** per available device.

### A.3 Availability

```
night_peak = P(charges overnight) × P(Wi-Fi) × P(undisturbed)
           = 0.72 × 0.86 × 0.97
           = 0.601
```

Per-device availability over the local clock is a smooth window centred on 02:00, reaching half-height near 21:30 and 06:30, decaying to a 5% daytime baseline:

```
night_weight(h) = 1 / (1 + exp((circular_distance(h, 02:00) − 4.5) / 1.0))
availability(h) = 0.05 + (0.601 − 0.05) × night_weight(h)
```

Global availability at UTC hour *t* integrates that over a continuous device-density function across longitude (21 weighted Gaussian clusters on a 2° grid):

```
global_availability(t) = Σ_lon density(lon) × availability(local_hour(lon, t))
```

Yielding: mean **25.7%**, minimum **14.1%**, maximum **40.8%**.

### A.4 Self-sufficiency

```
capacity_per_participant_per_day = mean_availability × tok/s × 86,400
                                 = 0.257 × 12.3 × 86,400
                                 = 273,700 tokens/day

headroom = 273,700 ÷ 30,000 = 9.1×
```

At the trough, substituting 0.141 for 0.257 gives 150,600 tokens/day, or 5.0×. Both are independent of enrolment, since capacity and membership are both linear in it.

### A.5 Scientific capacity

```
exaflops(N) = N × mean_availability × 299 GFLOPS
            = N × 0.257 × 2.99e11 ÷ 1e18

folding_parity_N = 2.4e18 ÷ (0.257 × 2.99e11) = 3.1e7 devices
full_fleet       = 1.20e9 × 0.257 × 2.99e11   = 92 exaFLOPS
fah_years_per_yr = 92 ÷ 2.4                   = 38
days_per_fah_yr  = 365 ÷ 38                   = 9.5 days
```

### A.6 Stated assumptions, all in one place

| Constant | Value | Confidence |
|---|---|---|
| Smartphone install base | 4.60e9 | Medium |
| Share ≥8GB RAM | 26% | Low-medium — hard to source precisely |
| Q4 weight footprint, 3B model | 1.80 GB | High |
| Usable bandwidth fraction | 0.55–0.62 | Medium |
| Thermal derate, 8h sustained | 0.70 | **Low — M0 measures this** |
| Ops per parameter per token | 2 | High |
| FP32 sustained fraction | 0.30–0.33 | **Low — M0 measures this** |
| Charges overnight | 72% | Low-medium |
| On Wi-Fi | 86% | Medium |
| Daytime availability | 5% | Low |
| Heavy user token consumption | 30,000/day | Medium |
| Folding@home peak | 2.4 exaFLOPS | Medium — reported, not audited |
| Large cluster peak INT8 | 200 exaOPS | Medium — 100k × ~1,979 TOPS |
| Cluster serving throughput | 3,000 tok/s/GPU | **Low — wide real-world range** |

Anything marked low confidence is either measured in M0 or presented with its sensitivity in [§7](#7-sensitivity-what-if-we-are-wrong).

---

## Appendix B: what we retract

For the record, the claims from the earlier draft of this project that this document withdraws:

| Previous claim | Corrected | Why |
|---|---|---|
| 2.2B phones can run a modern small model *today* | ~1.2B today; ~2.4B by 2030 | 8GB+ RAM is a minority of the installed base; the original figure is a projection |
| ~5,800 exaOPS available at any moment | ~20 exaOPS INT8-equivalent at full enrolment | Peak NPU TOPS is not achievable for batch-1 decode |
| 1.4% adoption (~30M) passes the largest AI data centre | Not reachable at any adoption level (~12B devices required) | Same bandwidth-bound error |
| At full adoption, ~70× the largest data centre | Below it, in raw operations, permanently | Same |
| One night of the full fleet > one year of Folding@home at peak | ~10 days of the full fleet ≈ one Folding@home-year | INT8 NPU figures were compared against FP throughput |
| A full year ≈ 2,000 Folding@home-years | ~38 Folding@home-years | Same |
| 95% overnight availability | 60.1% | The original ignored that availability is a conjunction of three behaviours |
| Availability floor ~6% | ~14.1% | An artefact of modelling geography as four point clusters |

Two of those revisions are upward. Most are sharply downward.

The reason to print this table rather than silently ship better numbers: the project's only real asset is that its numbers can be trusted. That is worth more than any of the claims we just deleted.

---

## Colophon

**Licence.** This document is released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The code in this repository is Apache-2.0.

**Reproduce every figure in this document:**

```bash
pip install numpy matplotlib
python analysis/compute_model.py
```

**Found an error?** That is the most useful thing you can do for this project. Open an issue: <https://github.com/OWNER/meridian-moonlight/issues>

**Accessibility note.** No figure in this project uses red as a signal colour. Roughly 8% of men — including this project's author — cannot reliably distinguish red from green, and infrastructure documentation should be legible to the people writing it.
