# Vision

*The short version. For the full argument with numbers and derivations, see [WHITEPAPER.md](WHITEPAPER.md).*

---

## The one-line pitch

**Your phone works for the world while you sleep — and everyone gets free AI in return.**

---

## Why

Capable AI runs almost entirely inside data centres owned by a handful of companies. That makes access something you buy, capability something that follows capital, and the infrastructure a chokepoint — commercially, politically, and during disasters.

Meanwhile the most widely distributed computing hardware ever manufactured is already in people's pockets, already paid for, and already plugged in every night with nothing to do.

## What

A free, open-source client that turns willing participants' machines — phones and desktops — into nodes of a global AI network.

- **Each machine runs a whole small model locally.** Never a fragment. Splitting one model across the internet fails on latency physics, so we don't attempt it.
- **The network never runs arbitrary code on your machine.** A job is a prompt plus a task-type ID from an audited catalogue — never a script, a binary, or a container. That removes mining, cracking, malware, and proxy abuse structurally rather than by policy. Its cost: the network can only compute what we have already implemented.
- **Contribution is gated to conditions nobody notices** — plugged in, on Wi-Fi, screen off, battery above 80%, device cool. One switch, always visible, turns it off.
- **Requests are answered on your own device first.** The network is the fallback, not the default.
- **Compute follows the moon.** Night circles the planet continuously, so the supply of idle charging phones migrates westward around the clock and never drops below roughly 14% of the fleet.
- **Two tiers, two jobs.** Phones are the mission — 1.2 billion of them, plugged in nightly. Desktops are the research instrument: a discrete GPU does the scientific work of about 32 phones, and 85% of the network's science capacity comes from the desktop tier.
- **The surplus goes to open science.** Members use about 11% of capacity. The rest is a research instrument — Folding@home parity at ~1.3 million gaming PCs, or ~31 million phones.
- **Contributors earn compute, not money.** Non-transferable credits that decay, earned by *hours of availability rather than horsepower*, so an old mid-range phone earns like a flagship. The free tier stays free regardless of balance.

## Principles

1. **Consent is the foundation.** Opt-in, transparent, revocable. Compute-sharing *is* the app's stated purpose — never buried, never bundled with something else.
2. **Costs the participant nothing they notice.** No battery drain, no cellular data, no heat, no slowdown. We publish our own thermal and battery measurements, including the bad ones.
3. **Privacy by architecture, not by policy.** Personal data never leaves the device. Local-first means most requests generate no log anywhere.
4. **Free forever for individuals.** No token, no wallet, no ads, no sale of user data or user access. Institutions and companies buy surplus batch capacity on a separate public ledger; contributors are never paid, which is what keeps them volunteers rather than unlicensed contractors.
5. **Open source, open protocol.** Anyone can audit what runs on their device. Anyone can build a compatible node — or fork the whole thing and leave us behind.
6. **Honesty is the strategy, not the style.** Trust is the only real asset. A project that inflates its numbers has already spent it.

## What this is not

Stating what physics forbids is what separates an infrastructure proposal from a whitepaper nobody technical will finish reading.

- **Not one giant brain.** Each node runs a complete model; the network never carries activations mid-forward-pass.
- **Will not train frontier models.** Federated fine-tuning of a small model, yes. Pre-training, never.
- **Throughput, not pooled power.** A million independent tasks — not one task made a million times faster.
- **Will not out-compute a data centre.** Data centres batch hundreds of users against one weight read; a phone can't. Per unit of hardware they win at inference, decisively. Our advantage is that the hardware is already bought and the marginal cost is zero.

Two claims from earlier drafts are retracted. **1.4% adoption surpassing the largest AI data centre** was built on peak NPU figures and is wrong by roughly 400×. **"Inference is deterministic so honest nodes agree exactly"** is true only on identical hardware, and it was load-bearing in three security documents. [Full table](WHITEPAPER.md#appendix-b-what-we-retract).

## Why this can win

Decentralised-compute projects exist — Acurast, Pocket Network, Destra, Exo Labs. Nearly all are crypto/DePIN plays that solve the participation problem with token rewards, and none has escaped the crypto niche into mainstream adoption.

The unclaimed position is the one that made SETI@home and Folding@home household names: **ordinary people contributing to something meaningful, for free, because it feels good and costs nothing.**

The moat is not the protocol — the protocol is meant to be copied. The moat is trust, simplicity, and a mission normal people want to join.

## Success, measured honestly

| | Test | Proves |
|---|---|---|
| **M0** | A phone *and* a desktop each run a model overnight and report measured throughput, watts, and thermals — plus a 60-second video of it working | The atomic unit works on both tiers, and the numbers in our own whitepaper are right |
| **M1** | 100 volunteer devices serve verified work to each other | The network works |
| **M2** | 10,000 devices; first science batch job; **measured** availability curve published | The follow-the-moon thesis is real, not modelled |
| **M3** | Protocol spec published; third-party nodes; governance in force; first research partner | It outlives its founder |

The M0 test is deliberately the one that could kill the project. If measured throughput comes back at a quarter of what we modelled, we say so publicly and revise — which is exactly how this version of the document came to exist.
