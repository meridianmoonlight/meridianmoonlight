# FAQ

Real questions, answered without marketing. If your question isn't here, [ask it](../../issues/new).

---

## For participants

### Will this drain my battery?

It shouldn't, because it only runs while your phone is plugged in, on Wi-Fi, with the screen off, above 80% charge, and not warm. If any of those stops being true, it stops immediately — mid-request if necessary.

The honest caveat: **we haven't measured this yet.** Nothing has been built. Milestone 0 exists specifically to produce overnight battery and thermal measurements on real devices, and we've committed to publishing them including if they're bad.

### Will it slow my phone down?

Not while you're using it — the gate requires the screen to be off, and picking your phone up ends the current work unit. You may notice your phone taking slightly longer to reach 100% charge.

### Will it damage my battery long-term?

**We don't know, and anyone who tells you they do is guessing.** Lithium-ion degradation depends on heat, charge cycling, and time at high state-of-charge. We gate on temperature and only run above 80% charge, which addresses the two we can control. But nobody has longitudinal data on multi-year nightly compute loads on phone batteries, and we won't have any for at least a year.

This is listed as an open assumption in the [whitepaper](../WHITEPAPER.md#14-how-to-falsify-this) and the [threat model](threat-model.md#battery-health). If you're not comfortable with an unquantified risk to your hardware, don't install it — that's a completely reasonable position and we'd rather say so than downplay it.

### Will it use my mobile data?

No. Wi-Fi only, and metered Wi-Fi hotspots are treated as cellular and excluded.

### What about my electricity bill?

There is one, and it's small but not zero. Running the SoC at load draws real watts that you pay for. We've committed to publishing measured watt-hours per night and the cost at typical residential rates once M0 produces the data. "It was plugged in anyway" is not the same as free, and we're not going to pretend it is.

### Can I see what my phone is doing?

Yes — a persistent notification while active, and a log of contributed work in the app. That's a requirement, not a feature: an app asking for space on your device that hides what it's doing has forfeited the right to be trusted.

### How do I stop?

One switch in the main view. No confirmation dialog that argues with you, no retention flow. Uninstalling is a complete exit with nothing left behind.

### Will other people's stuff run on my phone?

Yes — that's the point of the network, and here is exactly what that does and doesn't mean.

**What can run:** inference and a fixed set of audited scientific task types. Nothing else. **A job is a prompt plus a task-type ID — never a script, a binary, or a container**, so mining, password cracking, malware, and proxy abuse aren't possible on your device. Not "against policy" — there is no execution path for them. See [task-types.md](task-types.md).

**What we filter:** content policy is enforced at dispatch, before a job reaches you. Volunteers are never the filter.

**What you can turn off:** you can opt out of serving open requests entirely and contribute only to vetted research batch jobs.

**What we can't fix:** running a model requires the text in memory, so a determined node operator *could* read what their own device processes. Only hardware TEEs solve that and coverage is patchy. We mitigate structurally — you never learn who asked, and consecutive turns of a conversation go to different machines — but we're not going to promise privacy the architecture can't deliver. [Detail](threat-model.md#6-what-this-design-cannot-do).

### Do I get paid? Do I get tokens?

No, and there is no token, no wallet, no coin, and no plan for any. If you find a Meridian Moonlight token being sold anywhere, it's a scam and we'd appreciate a heads-up.

What you get is a free private AI assistant on your device and a share of a research instrument.

### But why not sell the compute and split the money with us?

We costed it, because this is the most common suggestion the project gets. Full workings in [`analysis/ECONOMICS.md`](../analysis/ECONOMICS.md).

**Your phone's spare compute is worth about $1.32 a year to you** after utilisation, verification overhead, and platform costs. Your electricity to produce it costs $1.58 in the US, $2.69 in the UK, $3.71 in Germany. **In most of the world you would be paying us to participate.** Even a deliberately optimistic scenario reaches only ~$8/year — about one hour of minimum wage, annually.

And a monthly payout of eleven cents against a $0.28 transaction fee means the fees exceed the payment. The only rail that makes micropayments that small work is a token.

There are worse problems than the arithmetic. Paying people would attach a cash bounty to [the one security problem we admit we haven't solved](threat-model.md#sybil-attacks) — right now a fake node earns nothing; under payment every fake node is revenue. It would make app-store approval harder, turn volunteers into paid contractors with tax and worker-classification consequences, and create a group of participants lobbying to let their phones run hotter for longer.

**What we do instead:** sell batch compute to institutions and corporations, but distribute it as a commons — hosting, development, and a published research grant pool, with open books. Contributors get priority routing, bigger models, and higher quotas: real value, no payment rails. And you can direct your notional share to a research project you choose.

If you think our price-per-TFLOP-hour assumption is far too low, it's one named constant — change it and re-run. The optimistic column already tests roughly five times our central figure.

### Is this crypto?

No. No blockchain, no token, no wallet, no yield, nothing to speculate on. The closest relatives are SETI@home and Folding@home.

---

## For skeptics

### Isn't a phone way too slow for this?

For serving AI, a phone is far less efficient than a data centre GPU, and we say so in the [whitepaper](../WHITEPAPER.md#24-and-one-limit-that-is-not-physics-but-is-real). A data centre reads each model weight from memory once and serves hundreds of concurrent users with it. A phone reads it once per token, for one user. Per unit of hardware they win decisively.

Our advantage isn't efficiency. It's that the hardware is already bought, the electricity is already being spent, and the marginal cost of the next token is zero.

### Your compute numbers look inflated.

They were. **An earlier draft of this project claimed 1.4% adoption would surpass the largest AI data centre on Earth. That claim was wrong by roughly 400× and we retract it** — the full table of retractions is [here](../WHITEPAPER.md#appendix-b-what-we-retract).

The error: quoting peak NPU TOPS for LLM inference. Decoding is bound by memory bandwidth, not arithmetic. A flagship advertising 45 INT8 TOPS sustains about 0.098 TOPS on a 3B model — a 457× gap.

The current numbers are generated by [one auditable script](../analysis/compute_model.py). Run it, change the assumptions, tell us what we got wrong.

### Isn't "1.2 billion capable phones" also inflated?

It might be — it's flagged as low-confidence. The installed-base share of ≥8GB-RAM handsets is genuinely hard to source precisely. The previous draft used 2.2 billion, which we believe is roughly a 2030 figure rather than a present-day one.

If you have better data, that's a valuable contribution. The [sensitivity analysis](../WHITEPAPER.md#7-sensitivity-what-if-we-are-wrong) shows how much it moves the conclusions.

### Why not just split a big model across phones?

Because generating each token requires activations to pass through every layer in sequence. If layers live on different devices, each token costs a network round trip per layer boundary. Data centre interconnects run at hundreds of GB/s and sub-microsecond latency; consumer internet is tens of milliseconds. That's five to six orders of magnitude, in exactly the dimension the workload is most sensitive to.

A 28-layer model split across 28 phones at 40ms per hop spends over a second of pure network latency per token. No software fixes that. Every node runs a complete model instead.

### Isn't this just Folding@home with extra steps?

Folding@home is the direct ancestor and we're happy to say so. Two differences: the substrate is far larger (~1.2 billion capable phones and ~920 million desktops, against ~1 million machines at Folding@home's peak), and this network also serves interactive AI back to its participants rather than only consuming their compute.

One notable similarity we've had to accept: the scientific work happens mostly on PCs, same as it always did. A discrete GPU does the science of about 32 phones, so [85% of our scientific capacity is the desktop tier](../WHITEPAPER.md#41-the-desktop-tier). The phones are what's new; the science is still mostly gaming rigs.

We're not claiming to have invented volunteer computing.

### You're centralised. So what's decentralised about it?

Nothing yet, and that's deliberate. Phases M0–M1 use a single coordinator, because peer discovery is a hard problem that adds nothing to proving the core idea works.

libp2p peer discovery starts in M2. The protocol spec ships in M3 so anyone can run their own coordinator without asking. **If that spec hasn't shipped by end of M3, this criticism was right and we failed** — it's a testable commitment, not a vibe.

### What stops a malicious node returning garbage?

Redundant execution on a sampled fraction with semantic comparison, plus reputation scoring. Details and residual risks in the [threat model](threat-model.md#malicious-or-faulty-nodes). We don't verify everything — that would cost 3× the compute — and we publish the sampling rate so the residual risk is visible.

### How do you stop Sybil attacks?

We don't, fully. Nobody has solved Sybil resistance without either a trusted identity registry or a costly stake, and we've ruled out stake. We use device attestation, slow reputation accrual through real work, and diversified verification quorums to **bound the damage** rather than prevent the attack. That's stated plainly in the [threat model](threat-model.md#sybil-attacks).

### Won't app stores just ban this?

Possibly. Background compute contribution has been grounds for removal, historically where it was concealed or bundled into an app pretending to do something else. Our position is that compute sharing is the app's entire stated purpose, disclosed in the listing, opt-in, and visible in a persistent notification.

That may not be enough. Mitigation: engage policy review early rather than shipping and hoping, and keep sideloading and F-Droid as a fallback.

### What about iOS?

iOS background execution limits effectively forbid this. An iOS node can realistically only contribute while the app is open and charging, making it a much weaker participant. Android is first and iOS is planned as a partial capability — we're not going to claim parity that the platform doesn't allow.

---

## For researchers

### Can I run a workload on this?

Not yet — there's no network. And when there is, there's a constraint you need to know about up front:

**You cannot submit code.** The network runs a fixed catalogue of [audited task types](task-types.md), because it never executes arbitrary code on a volunteer's machine. You submit *data and parameters* against an existing task type. If the work you need isn't in the catalogue, you request a new type, it gets a public review and a security audit, and it ships in a signed client release — weeks to months.

That is a real limitation and it rules out a lot of research. It's the price of being able to promise volunteers that their hardware can't be misused.

The shape that fits: **embarrassingly parallel** — millions of independent, bounded, verifiable tasks. Virtual screening, materials search, ensemble parameter sweeps, signal scans, independent-replica MD.

If your problem needs tight coupling between processors, this is the wrong instrument and we'll say so.

### What will it cost?

The intended model is that research bodies, universities, foundations, and nonprofits pay for batch capacity at rates far below cloud, because our marginal compute cost is zero. That revenue is what funds hosting and development.

**Full disclosure: no institution has agreed to pay for anything. There is no validated funding model yet.** The first partnership is an M3 deliverable.

### How much compute would I actually get?

Depends entirely on enrolment, and the [current numbers](../analysis/NUMBERS.md) are modelled rather than measured. At 31 million enrolled devices the network would continuously match Folding@home's peak (~2.4 exaFLOPS sustained). At 1 million devices it's ~0.08 exaFLOPS.

Treat these as an order-of-magnitude estimate with a published 4× uncertainty band until M0 replaces them with measurements.

### What about interruptions? Phones aren't reliable.

They're extremely unreliable, individually — the user picks it up, unplugs it, or it gets warm. The framework requires small work units, mandatory checkpointing, and idempotent execution. Long single trajectories are a poor fit; ensembles of independent replicas are a good one.

### Can I do federated learning on consenting users' data?

That's the capability no data centre can offer at any price, and it's an M3 target. The blocker for that class of research is privacy law and data-sharing agreements, not compute scarcity — which means the architecture is the unlock, not the scale.

It's also the highest-risk component in the design and ships last for that reason.

---

## About the project

### Who's building this?

One person, currently. That's stated plainly in the [governance doc](governance.md) rather than dressed up as a team. A benevolent-dictator model at this size, with public decisions and all discussion in public issues.

### How is this funded?

It isn't. M0–M2 have to be affordable to run essentially unfunded, which is achievable because at those scales the bandwidth bill is small.

### What's the business model?

Institutional batch-compute partnerships, plus grants. **Never** selling participant access, participant data, participant attention, or a token. Those commitments go in a published constitution at M3 with a deliberately hard process for changing them.

### Why should I trust you?

You shouldn't, yet. What you can do instead is check the work: the [compute model](../analysis/compute_model.py) is a few hundred lines of commented Python, every assumption is a named constant with its confidence stated, and the project's headline claim was retracted by its own authors with the arithmetic shown.

That's the only argument available at this stage, and it's the one we'd want if we were you.

### How can I help?

- **Find an error in the math.** Genuinely the most valuable thing right now.
- **Android/Kotlin work.** M0 is llama.cpp via JNI plus a foreground service with the contribution gate.
- **Benchmark a phone.** M0 needs measured tok/s, watts, and thermals across many device models.
- **Bring a workload** if you're a researcher with a parallel problem and no budget.

See [CONTRIBUTING.md](../CONTRIBUTING.md).
