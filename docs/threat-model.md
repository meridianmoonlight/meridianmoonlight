# Threat model

Adversarial analysis. What can go wrong, who benefits, what we do about it, and where we don't have an answer.

The section that matters most is [content liability](#content-liability). It is the risk most likely to end the project, and it is the one comparable proposals usually omit.

---

## Assets and adversaries

**What's worth attacking:**

| Asset | Why an attacker wants it |
|---|---|
| Result integrity | Poison scientific output; discredit the network |
| Model integrity | Steer the shared model's behaviour |
| Participant devices | Free compute for someone else's purpose; a botnet with a friendly installer |
| Participant privacy | Usage patterns, timing, location inference |
| Coordinator | Single point of control during the centralised phase |
| The project's reputation | One incident is sufficient to end a volunteer network |

**Who:** opportunistic freeloaders; vandals seeking notoriety; researchers with a competing result; a state actor interested in a network with nodes in every jurisdiction; and — the likeliest — a well-meaning participant who misconfigures something.

**Explicitly out of scope:** an adversary with physical access to a participant's unlocked device, and a compromised phone OS. We cannot defend those and won't pretend to.

---

## Malicious or faulty nodes

### Garbage results

**Attack.** A node returns plausible-looking but wrong output — random tokens, a cached response to a different prompt, or a deliberately corrupted scientific result.

**Mitigation.** Redundant execution on a sampled fraction with semantic comparison, plus reputation scoring, from the first version. Nodes disagreeing with consensus lose reputation and get sampled more heavily until excluded.

**Residual risk.** Sampling means most work is unverified. An attacker who is correct on sampled requests and wrong on the rest can persist. Countermeasure: sampling must be unpredictable to the node, and the sampling rate must be published so the residual risk is legible rather than hidden.

### Sybil attacks

**Attack.** Cheap identity creation. Manufacture thousands of node identities to dominate a verification quorum, farm reputation, or bias federated updates.

**Mitigation.**
- Platform device attestation where available (Play Integrity on Android), rate-limited per attestation.
- Reputation accrues slowly and only through sustained, verified, real work — it cannot be bought or rushed.
- Quorum selection weighted by reputation and diversified across network origin, ASN, and region.
- Anomaly detection on registration patterns.

**Residual risk. This is not solved.** Sybil resistance has never been achieved without either a trusted identity registry or a costly stake, and we have ruled out stake (no token) and are reluctant about a registry (privacy, centralisation). **We bound the damage rather than preventing the attack.** Anyone claiming to have solved this cheaply should be read skeptically, including us.

### Denial of service against the network

**Attack.** Flood the coordinator with registrations or requests; or enrol many nodes that accept work and never return it.

**Mitigation.** Rate limits per attestation and per origin; work timeouts with automatic reassignment; reputation penalties for accepted-but-unreturned work; a requester-side quota tied to contribution history.

### Using the network as an attack platform

**Attack.** Submit batch work that is actually password cracking, cryptocurrency mining, or traffic generation against a third party. The network becomes an unwitting botnet with a friendly installer.

**Mitigation.** This is why batch work is restricted to identified, accountable institutions with reviewed workloads. Workload vetting is a governance gate, not a technical one — a general-purpose compute network that accepts anonymous jobs is a botnet by definition, whatever its intentions.

**Residual risk.** Vetting doesn't scale without a process, and the process is a bottleneck we are choosing on purpose.

---

## Model poisoning

**Attack.** During federated fine-tuning, contribute crafted gradients to install a backdoor, degrade quality, or bias output on a chosen topic.

**Mitigation.**
- Robust aggregation (trimmed mean / median-based) discarding outlier updates.
- Per-update norm clipping so no single contribution can dominate.
- Holdout evaluation gates: no aggregated update is promoted without passing a benchmark suite the contributors cannot see.
- Staged rollout with automatic rollback on regression.
- Contribution weighted by node reputation.

**Why this ships last.** Federated fine-tuning is deferred to M3 specifically so that verification and reputation have real operating history before anything is allowed to modify the shared model. Shipping it early would be the single most dangerous ordering mistake available to us.

**Residual risk.** A patient attacker with many reputable nodes contributing subtly biased updates over a long period is difficult to detect. Holdout evaluation catches capability regressions, not narrow targeted bias.

---

## Content liability

**This is the risk most likely to end the project.**

### The problem, stated plainly

Routing an anonymous third party's prompt to a volunteer's phone means **a stranger's content is processed on a private individual's hardware, in their home, under their jurisdiction, on their internet connection.**

Some fraction of arbitrary prompts submitted to any public AI service will be illegal to process somewhere. At scale that fraction is not hypothetical. The participant — a volunteer who ticked a box to help science — is the person whose device did the processing and whose IP address appears in the logs.

A local content classifier reduces incidence. It cannot be relied upon, it will have both false positives and false negatives, and it does not change who is holding the device.

### Three options

**Option A — route third-party inference, with content filtering.**
Maximum utility; delivers the "free AI for people whose phone can't run a model" promise directly. Places an unbounded legal and moral liability on volunteers who cannot evaluate it.

**Option B — inference stays strictly local; the network carries only vetted batch work.**
A participant's device runs a model *for its owner only*. Shared capacity goes exclusively to batch jobs from identified, accountable institutions with reviewed workloads. **No volunteer's phone ever processes an anonymous stranger's prompt.**

**Option C — Option B, plus an explicit opt-in tier** for participants who choose to serve third-party inference, with filtering, genuinely informed consent (not a EULA), and jurisdiction awareness in routing.

### Recommendation

**Option B for M0–M2. Option C only with an explicit, published safety design and legal review.**

The cost is real and worth naming: this defers the most emotionally compelling part of the pitch — free AI for people whose device cannot run a model. That is the part that makes people want to join.

We think it is the right trade anyway. The project cannot ask volunteers to accept legal exposure they don't understand, and one incident in year one ends everything. A network that survives to year three can revisit this from a position of institutional strength; one that gets a volunteer raided cannot.

**This is the most consequential open decision in the design and is not considered settled.** Argue with us in the issues.

---

## Privacy

### Metadata leakage

**Attack.** The coordinator, or a network observer, infers participant behaviour from request timing, volume, and routing.

**Mitigation.** Local-first architecture means most requests generate no coordinator record at all. Minimum viable retention. The log schema and retention period are published as a public interface, and changing them requires the same scrutiny as a protocol change.

**Residual risk.** During the centralised phase the coordinator is a genuine observation point. P2P transfer from M2 reduces but does not eliminate it.

### Deanonymisation of requesters

**Attack.** A malicious node correlates prompts it serves with other signals to identify requesters.

**Mitigation.** Under Option B this risk largely doesn't exist, because nodes don't serve third-party prompts. Under Option C it becomes a first-class design problem requiring requester-node unlinkability, and shipping Option C without solving it would be irresponsible.

### Model weight extraction

**Attack.** Extract model weights from a participant's device.

**Assessment.** Trivially possible, and a non-issue by construction: only openly licensed weights are distributed. There is nothing to steal.

---

## Platform, legal, and reputational

### App store removal

**Risk.** Background compute contribution has been grounds for removal — historically where it was *concealed* or bundled into an app that appeared to do something else.

**Position.** Compute sharing is the app's entire stated purpose, declared in the store listing, opt-in at first run, and visible in a persistent notification while active. On Android this is a legitimate foreground service.

**Residual risk. Genuine, and we may be wrong.** Policy is applied at reviewer discretion and can change. Mitigation: engage policy review early rather than shipping and hoping; keep a sideloadable build and F-Droid distribution as a fallback.

### Energy cost and honesty

**Risk.** "The phone was plugged in anyway" does not make the electricity free. Running an SoC at load draws real watts paid for by the participant.

**Commitment.** Measure and publish marginal watt-hours per participant per night and marginal cost at typical residential rates, from M0 onward. **If the number is embarrassing, publishing it is still the deal.** A project whose entire strategy is trust does not get to hide its cost to participants.

### Battery health

**Risk.** Sustained overnight load across years degrades battery capacity in ways we cannot currently quantify.

**Status.** An open assumption. No longitudinal data exists and none will for a year. Mitigations that don't need data: gate at ≥80% charge, stop on thermal rise, cap nightly duty cycle, and publish what we learn as we learn it.

### Reputational single point of failure

**Risk.** One incident — a volunteer's device implicated in something, a battery damaged, a security breach — ends a volunteer network regardless of the technical merits.

**Mitigation.** Conservative defaults everywhere, the Option B content policy, a published incident response process, and radical transparency about problems. The projects in this lineage that lasted did so by being boring and trustworthy for a very long time.

---

## Coordinator compromise

**Attack.** An attacker who controls the coordinator can misroute work, forge verification outcomes, harvest metadata, or push a malicious model manifest.

**Mitigation.**
- Model weights distributed with published hashes; the client verifies before loading and refuses on mismatch.
- Client releases signed and reproducible; the app never accepts executable code from the coordinator, only data.
- Nodes enforce their own gate locally — the coordinator cannot instruct a device to override its own contribution conditions.
- P2P discovery from M2 reduces the coordinator's authority to brokering.
- Protocol spec at M3 means anyone can run a competing coordinator, which is the real structural mitigation.

**Residual risk.** During M0–M1 the coordinator is a genuine single point of trust. Stating this is the mitigation available at that stage.

---

## Reporting a vulnerability

See [SECURITY.md](../SECURITY.md). Please report privately first. We will credit you unless you ask us not to.

---

## Revision policy

This document changes when we learn something. Material changes are noted in the git history and, where they affect participants, announced.

If you think a risk here is understated — or that one is missing — [open an issue](../../issues/new). Being told we've underestimated something is more useful than being agreed with.
