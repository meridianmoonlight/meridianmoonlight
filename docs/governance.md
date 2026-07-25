# Governance

A network asking for space on a million personal devices owes those people a say in it. A project claiming to be "owned by no one" has to mean that structurally, not aspirationally.

---

## Where we actually are

**One person. Benevolent dictator. Stated plainly rather than dressed up.**

Pretending to have a governance structure at this size would be theatre, and theatre is exactly what erodes the trust this project runs on. What we commit to *now*:

- **All decisions in public.** Design discussion happens in issues, not in private. If a decision was made off-platform, it gets written down publicly with the reasoning.
- **Reasoning published, not just outcomes.** Including for decisions that turn out badly.
- **Retractions in public.** The project's headline claim was retracted in its own whitepaper, with the arithmetic. That's the standard.
- **Permissive licence from day one.** Apache-2.0 code, CC BY 4.0 docs. The right to walk away with all of it exists already.

---

## What ships by M3

These are deliverables with a milestone attached, not intentions.

### Open protocol specification

A third party must be able to build a compatible node and run a competing coordinator **without permission from us**. Not a courtesy — the structural guarantee that makes everything else credible.

**This is the falsifiable one: if the spec has not shipped by the end of M3, the "centralised scaffolding" defence was a rationalisation and we failed.**

### Contributor governance

An explicit path from contributor → committer → maintainer → decision-maker, with the criteria written down. No permanent inner circle by default.

### Legal structure

A non-profit or foundation holding the trademark, the domain, and the app store listings — so the project cannot be quietly sold, and so no single person's circumstances can end it.

### A published constitution

Commitments that are deliberately hard to change:

1. **Free forever for individuals.** No paid tier for participants, no premium features, no usage caps sold back.
2. **No token, no coin, no wallet.** Not now, not later, not as a "governance token."
3. **No advertising.** Anywhere. Ever.
4. **No sale of user data.** Not aggregated, not anonymised, not "shared with partners."
5. **No dark patterns.** Consent is informed and specific; withdrawal is one switch with no argument.
6. **Compute-sharing is always the stated purpose.** Never bundled into an app that appears to do something else.
7. **Participant experience outranks paying workloads.** Named explicitly because [the pressure will be real](../WHITEPAPER.md#103-the-honest-gap): if institutional batch work becomes the revenue source, someone will eventually propose prioritising it. This makes that trade-off a public decision rather than a quiet one.
8. **Measurements get published, including bad ones.** Thermals, battery, energy cost, availability.
9. **The free floor is unconditional.** Credits buy priority and headroom, never access. *If the free tier ever degrades to make credits attractive, the project has failed at its purpose.*
10. **Credits are never currency and never votes.** Non-transferable, non-purchasable, non-redeemable, decaying. Tying governance influence to accumulated credits is prohibited.
11. **Contributors are never paid in money.** Reciprocation is in capability. This is what keeps them volunteers rather than unlicensed contractors, and [the arithmetic that makes cash pointless anyway is published](../analysis/ECONOMICS.md).
12. **Paid work is surplus-only, and buying does not buy influence.** The nine rules in [economy.md](economy.md#hard-rules-on-paid-work) are constitutional, in particular: public ledger, public buyer register, no exclusivity, no roadmap or routing influence, and a 25% single-buyer revenue cap.
13. **The network never executes arbitrary code on a volunteer's machine.** Layer 0. Adding a general-purpose runtime — including a sandboxed one — requires the full amendment process, on every tier.

### The task-type catalogue is a governance artefact

Because [Layer 0](../WHITEPAPER.md#35-layer-0-and-the-task-type-catalogue) means the network can only compute what we have implemented, **the maintainers decide what the network is capable of.** That is more power over the project's purpose than the maintainers of most open-source projects hold, and it needs constraining rather than assuming good faith.

Every new [task type](task-types.md) therefore requires a public request, a minimum 14-day comment period, a published security review against fixed acceptance criteria, and a signed release in which participants re-confirm consent to the new work their device may accept. **Paying buyers cannot accelerate this and cannot commission a private task type.**

Refusals of buyers or workloads are logged publicly with a reason — which is also the accountability mechanism against refusing for bad ones.

**Amendment process:** deliberately slow and public. Supermajority of maintainers, a mandatory public comment period, and a written rationale. Any amendment weakening 1–6 should be practically impossible — and if a future steward manages it anyway, that's what the fork right is for.

### A fork right that actually works

A right to fork is meaningless unless the mechanics exist:

- **Permissive licence** — already in place.
- **Documented protocol** — M3.
- **Portable participant data** — export in a documented format.
- **No trademark trap** — the name is protected, but the code, protocol, docs, and figures are free. Fork the network, pick your own name.
- **Reproducible builds** so a fork can be verified as a fork.

If the stewards of this project go bad, the network should be able to leave them behind. That's the actual test of "owned by no one," and it's the only accountability mechanism that doesn't depend on our continued good behaviour.

---

## Decision-making, in the interim

| Decision type | Who | How |
|---|---|---|
| Bug fixes, docs, tests | Any contributor | PR + review |
| Feature work inside an agreed milestone | Contributor | PR + maintainer review |
| Architecture changes | Maintainers | Public issue, written rationale, ≥7 days |
| Anything touching the contribution gate | Maintainers | Public issue, ≥14 days, conservative default wins |
| Constitution changes (post-M3) | Supermajority | Public comment period, written rationale |
| Security fixes | Maintainers | Private until patched, then full disclosure |

The contribution gate gets a longer window than architecture on purpose. It is the promise the whole project rests on, and the correct bias when uncertain is always toward contributing *less*.

---

## Conflicts of interest

Anyone with a financial interest in a decision — a partnership, a funding source, employment by an interested party — discloses it in the relevant issue before participating. This applies to maintainers first.

If the project ever takes institutional money, the terms get published.

---

## What happens if the founder disappears

Currently: the project stops, and the licence means someone else can pick it up.

That is a real single point of failure, and removing it is what "proof it outlives its founder" means as the M3 success condition. The legal structure, the protocol spec, and more than one maintainer with commit and release access are the components. Until all three exist, this risk stands and is stated rather than hidden.
