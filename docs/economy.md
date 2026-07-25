# The compute economy

*How contribution and access balance without money, tokens, or speculation — and how corporate money enters without capturing the network.*

Two ledgers that never touch:

| | Contributor ledger | Money ledger |
|---|---|---|
| Unit | Compute credits | Ordinary currency |
| Who earns / pays | Volunteers earn | Institutions and corporations pay |
| Can it be exchanged? | Never | Normally |
| Where it goes | Priority, headroom, batch submission | Hosting, audits, development, grants |
| Public? | Individual balances private | **Every transaction published** |

Contributors are never paid, which is what keeps them volunteers rather than unlicensed contractors — a distinction with real legal weight in most jurisdictions.

---

# Part 1 — The contributor ledger

## The principle

**You earn compute by giving compute.** Nothing more, nothing less.

Credits are a *unit of participation*, not a unit of value. They cannot be bought, sold, transferred, or cashed out. They are not a currency, not a security, and not an asset. They exist for one purpose: to let the network allocate scarce capacity to the people who help create it.

This is what makes them compatible with the founding commitment. There is still no token, no wallet, and no ads — because credits never leave the account that earned them and never have a price.

## The free floor comes first

**Every person gets meaningful free access regardless of whether they contribute anything.**

Someone with a five-year-old phone, or no phone to spare, or no interest in running a node, still gets a working AI assistant. Credits buy *priority and headroom* — never access itself.

**If the free tier ever degrades to make credits attractive, the project has failed at its purpose.** That is the line, and it is a hard constraint in [the constitution](governance.md#a-published-constitution).

## Earning

Credits accrue for **verified** work only. Unverified results earn nothing — which means [canaries and re-derivation](threat-model.md#2-verification-how-we-know-the-work-is-real) gate the entire economy.

### Credit for availability, not horsepower

This is the most important design choice in the whole system.

Credits are weighted by **hours of reliable contribution**, not by raw throughput. A four-year-old mid-range phone contributing every night earns comparably to a current flagship doing the same — and, now that desktops are the primary tier, **a 24GB graphics card earns exactly what that old phone earns.**

The alternative — paying by tokens generated — would systematically reward whoever owns the best hardware, meaning the people who least need free AI would accumulate the most access to it. For a project whose reason to exist is serving people locked out by cost, that would be a quiet betrayal of the mission. Availability is the contribution that actually matters anyway: the network's whole thesis is *coverage across time zones*, not peak performance.

#### The objection this invites, and why the answer is not more credits

If a 24GB card earns no more than an old phone, why would anyone contribute the expensive machine? It is a fair question and it got sharper when [the model ladder](../analysis/LADDER.md) showed that the flagship capability depends on a small pool of exactly those cards.

The answer is not to pay them more credits, for three reasons:

1. **It would invert the mission.** Paying by throughput hands the most free AI to whoever already owns the best hardware — the people who least need it.
2. **Recognition can carry the load instead.** Public acknowledgement weighted by contribution is explicitly permitted below; what is forbidden is letting it affect *allocation*. Folding@home recruited enthusiast hardware for two decades on exactly that basis.
3. **The capability is its own reward.** Someone hosting the 32B model gets to use the 32B model. So does everyone else — that is the point — but they are not giving something away and receiving nothing back.

**This remains the least settled part of the design.** If the flagship pool fails to materialise, the honest response is to say so and revisit, not to quietly introduce throughput-weighted earning and hope nobody notices the mission drifting.

It also has a security dividend. Because credits track hours rather than throughput, [a fake fleet gains nothing from claiming fast hardware](desktop-security.md#behavioural-fingerprinting) — it would have to genuinely stay online and genuinely pass canaries.

### What earns

| Contribution | Credit |
|---|---|
| Verified inference served | Base rate per node-hour of availability |
| Overnight batch science work | Same base rate — research is not worth less than chat |
| Sustained reliability | Modest multiplier after weeks of consistent uptime |
| Failing a canary task | Forfeits recent earnings and resets reputation |

### Daily ceiling

Each device earns up to a fixed daily maximum. This caps the payoff from running a device flat-out, blunts the incentive to build a fake fleet, and keeps a thousand-device operator from dominating allocation.

## Spending

| What credits buy | Why it's scarce |
|---|---|
| Priority in the queue | Capacity is finite during peak hours |
| Access to larger models | 8B costs more network resource than 3B |
| Extended context length | Memory-bound on contributing devices |
| **Submitting your own batch job** | The genuinely scarce thing — and the reason a researcher would contribute |

That last row is where this becomes a real economy. A researcher with a parallel workload and no budget can *earn* their compute by contributing devices, or by getting their institution's idle fleet to contribute. Compute in, compute out, no invoice.

**With one hard limit worth being explicit about:** submitting a batch job means submitting *data and parameters against an existing [task type](task-types.md)*. It does not mean submitting code. If the work a researcher needs isn't in the catalogue, credits cannot buy it — they have to [request a new task type](task-types.md#requesting-a-new-task-type) and wait for a release. That is a real constraint on this promise and it is stated in the catalogue too.

## Credits decay

Balances decay on roughly a 90-day half-life. Three reasons, all deliberate:

1. **It keeps them from looking like an asset.** A permanent balance accumulates the psychology of savings. A decaying allowance stays obviously what it is — a usage budget.
2. **It kills any secondary market.** Nothing worth informally trading has a short shelf life and no transfer mechanism.
3. **It rewards continuing contribution** rather than a single burst years ago.

## What is deliberately excluded

- **No transfers between accounts.** Not gifts, not pooling, not delegation. The moment credits move, they have a price.
- **No purchasing credits.** Money cannot enter the contributor side of the ledger at any price.
- **No cash-out, ever.** There is nothing to redeem.
- **No credits as votes.** Governance stays separate. Tying influence to accumulated credits builds a plutocracy and turns the credit into something a regulator would reasonably call a security.
- **No leaderboards tied to allocation.** Public recognition is fine and motivating; it must not affect who gets served.

## Interaction with security

Adding credits reintroduces some incentive to game the network, which the original threat model relied on being absent. Three properties contain it:

- **Non-transferable.** A fake fleet's credits are stranded in accounts that cannot sell or consolidate them. The yield of a successful Sybil attack is near zero.
- **Daily caps.** Bounded upside per device, so scale doesn't multiply the payoff linearly.
- **Verification gates earning.** Credits require passing redundant execution and canary checks, so a lying node earns nothing and loses reputation.

The net risk is meaningfully higher than zero but far below a token economy, where the attack directly produces a sellable asset. [DESKTOP_SECURITY](desktop-security.md#reframe-1-sybil-buys-identity-not-capacity) works through what this leaves an attacker.

---

# Part 2 — The money ledger

## Why corporate money is welcome here

The scenario is worth taking seriously: instead of building data centres and buying frontier-lab subscriptions, large companies route their parallelisable workloads through the network and pay into it.

That is a real revenue line, and it is the intended primary funding source. The network has genuine things to sell:

- **Overnight batch capacity** at a marginal compute cost of zero to us.
- **A capability no data centre can offer at any price:** [federated analysis over data that cannot legally be centralised](../WHITEPAPER.md#82-at-31m-devices-and-beyond-a-research-instrument).
- **Association with a public-good network** — reach and goodwill alongside the compute.

We are not squeamish about corporate buyers. We are careful about what they can buy.

## Why the money is not divided among contributors

The obvious next step — split the payments across the network — was costed rather than dismissed. Full workings in [`analysis/ECONOMICS.md`](../analysis/ECONOMICS.md).

**A phone's spare compute is worth about $1.32 a year to its owner** after utilisation, verification overhead, and platform costs. Their electricity to produce it costs $1.58 in the US, $2.69 in the UK, $3.71 in Germany. **In most of the world the participant would be paying to contribute.** A deliberately optimistic scenario reaches about $8/year — roughly one hour of minimum wage, annually. And a monthly payout of eleven cents against a $0.28 transaction fee means the fee exceeds the payment.

The aggregate, meanwhile, is transformative. Divided per head it is pennies; kept whole it funds an institution. So it is kept whole.

Beyond the arithmetic, paying contributors would [attach a cash bounty to the one security problem we admit is unsolved](desktop-security.md#reframe-1-sybil-buys-identity-not-capacity), make app-store approval harder, convert volunteers into contractors, and create a constituency lobbying to weaken the contribution gate. The [fairness instinct behind the suggestion is right](../analysis/ECONOMICS.md#what-the-instinct-behind-the-question-gets-right); cash at this magnitude cannot honour it.

**Contributors are reciprocated in capability, not currency** — that is what Part 1 is.

## Buyer tiers

| Tier | Who | Rate | Priority |
|---|---|---|---|
| **Public research** | Universities, public-health bodies, non-profits, open-science projects | Lowest published rate; free allocation available by application | Highest of the paid tiers |
| **Commercial** | Companies of any size | Standard published rate | Below public research |
| **Sponsor** | Buyers funding the commons beyond their own usage | Standard rate plus contribution; acknowledged publicly | **No priority advantage whatsoever** |

Rates are **published**, identical for every buyer inside a tier, and not negotiable in private. A buyer's size does not move their rate or their queue position.

The sponsor tier exists because the goodwill value is real and some buyers will want to pay for more than they consume. It deliberately buys **recognition and nothing else** — the moment money buys queue position, the network is for sale.

## Hard rules on paid work

These are constraints, not preferences, and they belong in [the constitution](governance.md#a-published-constitution):

1. **Surplus only.** Paid work runs in capacity above what participants need. The [free floor is reserved first, always](#the-free-floor-comes-first).
2. **Never preempts free access.** A paying job cannot displace a running free request, and cannot push free requests below the reserved floor even at peak.
3. **Public buyer register.** Every paying buyer is named, with what they bought and what they spent. Anonymous corporate compute purchasing is not available at any price.
4. **Public ledger.** Every payment in and every expense out, posted permanently and reconciled quarterly.
5. **No exclusivity.** No buyer gets sole access to a capability, a task type, a region, or a time window.
6. **No influence.** Paying buys compute. It does not buy routing preference, roadmap influence, governance participation, a board seat, or a veto. Buyers are customers, not stakeholders.
7. **Concentration cap.** No single buyer may exceed **25%** of annual revenue. Approaching the cap triggers a public disclosure and a plan to reduce dependence. A funder large enough to end the project by leaving is a governance problem regardless of their conduct.
8. **Catalogue only.** Buyers submit data against [existing task types](task-types.md). Paying does not accelerate a new task type past its public review, and does not buy a private one.
9. **Refusal is allowed and recorded.** The project may decline a buyer or a workload. Refusals are logged publicly with a reason — which is also the accountability mechanism against refusing for bad reasons.

## Where the money goes

Priority order, published quarterly against actuals:

1. **Infrastructure** — coordinator hosting, bandwidth, model distribution.
2. **Security** — external audits, bug bounties once there is money for them.
3. **Development** — maintainer time, which is currently unfunded.
4. **Research grant pool** — free allocation for researchers who cannot pay, funded from commercial revenue. This is the point of the whole arrangement: commercial buyers subsidise public science.
5. **Reserve** — enough runway that losing the largest buyer is survivable.

**Nothing goes to contributor payouts, equity, or dividends.** There are no shares to hold.

## The honest gaps

- **No institution or company has agreed to pay for anything.** There is no validated funding model. M0–M2 must be affordable to run essentially unfunded, which is achievable because at those scales the bandwidth bill is small.
- **The sponsor tier is a marketing budget, not an infrastructure budget.** Those are smaller, less durable, and first cut in a downturn. Revenue concentrated there is fragile revenue.
- **Rule 6 will be tested.** A large buyer will eventually ask for something the rules forbid, and the answer has to be no in public. That is easier to write now than to do later, which is exactly why it is written now.
- **The 25% cap is a guess.** It may be too loose to matter or too tight to be practical.

---

## Open questions

Honest list of what isn't decided:

- Should batch-job submission require an identity check, given it's the most abusable spend?
- Does the daily credit cap need to scale with network size, or stay fixed?
- Should buyers be able to *donate* purchased capacity to public researchers directly, rather than only via the grant pool?
- What happens to credits if someone's only phone breaks — is there a hardship allowance?
- Is 90 days the right half-life, or does it punish irregular contributors unfairly?
- Is 25% the right concentration cap?
- Who audits the public ledger before there is money to pay an auditor?

These get decided in the open, before implementation, in the M3 governance work.
