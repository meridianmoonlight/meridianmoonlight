# Contributing

This project is a proposal with no code yet. That makes now an unusually good time to change its direction.

---

## The most valuable contribution: tell us we're wrong

Seriously. Above code, above docs, above everything.

Every number this project publishes comes from [`analysis/compute_model.py`](analysis/compute_model.py):

```bash
pip install numpy matplotlib
python analysis/compute_model.py
```

Assumptions are named constants at the top with their basis and confidence stated inline. The ones we have the least confidence in, flagged by us:

| Constant | Value | Why we're unsure |
|---|---|---|
| `THERMAL_DERATE` | 0.70 | Sustained vs burst over an 8-hour run on a charging device. Barely studied. |
| `fp32_sustained_fraction` | 0.30–0.33 | Mobile GPU sustained FP32 over hours is almost undocumented — nobody runs phones this way |
| `SHARE_RAM_8GB_PLUS` | 0.26 | Installed-base RAM distribution is hard to source precisely |
| `DC_TOKENS_PER_SEC_PER_GPU` | 3000 | Real-world serving throughput spans a wide range |

If you can improve any of these — with a source, a measurement, or an argument — [open an issue](../../issues/new). If you find an outright error, that's the best possible outcome for us.

The project's own headline claim was retracted in its whitepaper with the arithmetic shown ([Appendix B](WHITEPAPER.md#appendix-b-what-we-retract)). That is the standard, and being corrected is not a loss here.

---

## What the project needs

### Skeptics
Read the [whitepaper](WHITEPAPER.md) and the [compute model](analysis/compute_model.py). Attack the assumptions, the units, and the comparisons. Especially: are we still conflating INT8 and FP32 anywhere? Is the batching asymmetry stated strongly enough?

### Android / Kotlin engineers
[M0](docs/MILESTONES.md#m0--one-node-lives) is llama.cpp via JNI plus a foreground service with a charging/Wi-Fi/idle gate. For the right person this is a weekend project, and it is the single thing blocking everything else.

### Anyone with an Android phone and patience
[M0 needs measured](docs/MILESTONES.md#8-help-wanted-benchmark-your-phone) tok/s, sustained watts, and thermals across many device models. That table cannot be built by one person with one phone, and it's what replaces the modelled figures with real ones.

### Backend engineers
Node.js + TypeScript coordinator: registry, router, verifier. See [protocol-spec.md](docs/protocol-spec.md).

### Frontend engineers
The live node map is both a diagnostic tool and the main recruiting asset. React + Vite. Use the protan-safe palette — see [design constraints](#design-constraints) below.

### Researchers
If you have an embarrassingly parallel problem and no budget, that is the entire point of the surplus capacity. Tell us what shape your workload is, even now — it shapes the batch framework.

### Security people
The [threat model](docs/threat-model.md) has explicitly unsolved sections. [Sybil resistance](docs/threat-model.md#sybil-attacks) is bounded, not solved. The [content-routing question](docs/threat-model.md#content-liability) is the most consequential open decision in the design and we would genuinely like to be argued with about it.

---

## Ground rules

### Honesty is the product

This project's only real asset is that its numbers can be trusted. Practical consequences for contributions:

- **No unmeasured performance claims.** Label modelled figures as modelled.
- **State uncertainty.** "We think X, confidence low, here's why" beats false precision.
- **Publish bad results.** Especially thermal, battery, and energy measurements. This is a written commitment, not a preference.
- **Don't quietly fix an error.** If a published number was wrong, correct it *and* say it was wrong.

### Conservative defaults on anything touching a participant's device

When uncertain about the [contribution gate](ARCHITECTURE.md#33-the-contribution-gate), contribute *less*. A gate that is too strict costs capacity. A gate that is too loose costs trust, and trust is not recoverable.

### Design constraints

- **No red as a signal colour.** Anywhere — figures, dashboards, UI, status indicators. Roughly 8% of men, including this project's author, cannot reliably distinguish red from green. The palette is defined at the top of [`compute_model.py`](analysis/compute_model.py): blue `#3B5BDB`, teal `#0E9DA8`, amber `#E8912B`, magenta `#B3399E`, slate `#7A88A8`. Separate categories by luminance as well as hue so figures survive greyscale.
- **Never dark-pattern the withdrawal flow.** One switch, no argument, no retention prompt.
- **Figures are generated, never hand-edited.** Everything in `docs/figures/` comes from the model script. Edit the script.

---

## Practical

### Issues before PRs
For anything beyond a typo, open an issue first. Saves you work if the direction is wrong.

### Branches and commits
Branch from `main` as `m0/short-description` or `fix/short-description`. Imperative commit subjects; explain *why* in the body when it isn't obvious.

### Regenerating figures
If you change `compute_model.py`, re-run it and commit the regenerated `docs/figures/*.png`, `analysis/NUMBERS.md`, and `analysis/numbers.json` in the same commit. They must never drift out of sync with the model.

### Documentation changes that move a number
If a change moves a published figure, update every place it appears: `WHITEPAPER.md`, `README.md`, `site/`, and `analysis/NUMBERS.md`. Grep for the old value before committing.

### Licensing
Code contributions are Apache-2.0. Documentation is CC BY 4.0. By contributing you agree to license your work under those terms.

---

## Reporting a security issue

Do not open a public issue. See [SECURITY.md](SECURITY.md).

---

## Code of conduct

[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Short version: be someone people want to build with. Vigorous disagreement about technical substance is the point of this repo; contempt for people is not.
