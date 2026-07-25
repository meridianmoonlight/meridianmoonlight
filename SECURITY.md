# Security policy

## Reporting a vulnerability

**Do not open a public issue.**

Email **security@meridianmoonlight.com**, or use GitHub's [private vulnerability reporting](../../security/advisories/new).

Please include: what you found, how to reproduce it, what an attacker could do with it, and how you'd like to be credited (or that you'd rather not be).

**What to expect:** acknowledgement within 72 hours; an initial assessment within 7 days; and if we have to go quiet, we'll tell you why rather than just going quiet.

We will credit you in the advisory and the release notes unless you ask us not to. There is no bug bounty — this project has no funding.

## Scope

**In scope, once the relevant components exist:**

- The Android client, particularly anything that could bypass the [contribution gate](ARCHITECTURE.md#33-the-contribution-gate) — that gate is the promise the project rests on
- The coordinator: registration, routing, verification, reputation
- Protocol design flaws ([protocol-spec.md](docs/protocol-spec.md))
- Model distribution integrity — hash verification bypass, malicious manifest acceptance
- Anything letting a coordinator instruct a node to override its own gate (this is a hard [protocol invariant](docs/protocol-spec.md#53-nodegate))
- Anything exposing participant data or enabling deanonymisation
- Supply chain: build reproducibility, release signing

**Out of scope:**

- An adversary with physical access to an unlocked participant device
- A compromised phone OS
- Anything in the [threat model](docs/threat-model.md) already documented as a known residual risk — though a *better attack* against a known-bounded risk, or evidence a bound is weaker than we claimed, is very much in scope
- Findings against the website that don't affect participants (it's static HTML with no backend)

## Known unsolved problems

We would rather tell you than have you spend a weekend rediscovering them. These are documented, not secret:

- **[Sybil resistance](docs/threat-model.md#sybil-attacks) is bounded, not solved.** No cheap solution exists without a trusted registry or a costly stake, and we've ruled out stake.
- **Verification sampling means most work is unverified.** The sampling rate is published for exactly this reason.
- **The coordinator is a single point of trust through M1.** Reduced from M2 (P2P), structurally addressed at M3 (open protocol, competing coordinators).
- **Semantic agreement scoring for text verification is unspecified.** See [protocol-spec.md §7](docs/protocol-spec.md#7-verification).
- **The [content-routing question](docs/threat-model.md#content-liability) is unresolved.** Current recommendation is the conservative option; it is not settled.

A demonstration that one of these is *worse than we've claimed* is a valid and welcome report.

## Current status

**No code exists yet.** There is nothing to attack but the design, and design-level findings are the cheapest kind to fix. If you can break the [protocol sketch](docs/protocol-spec.md) or the [threat model](docs/threat-model.md) on paper, now is by far the best time.

## Disclosure

Coordinated disclosure. We'll agree a timeline with you — 90 days by default, faster where a fix is simple, longer only with your agreement.

Once fixed we publish a full advisory including what went wrong and what we missed. Consistent with [how this project handles being wrong about anything else](WHITEPAPER.md#appendix-b-what-we-retract).
