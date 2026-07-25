# measurements/

Real numbers from real devices. **This directory is currently empty, and that is the single most important gap in the project.**

Every performance figure we publish today is *modelled* by [`analysis/compute_model.py`](../analysis/compute_model.py). [Milestone 0](../docs/MILESTONES.md#m0--one-node-lives) exists to replace them with measurements taken here.

## What goes here

| File | Contents |
|---|---|
| `DEVICES.md` | The headline table: one row per device model, measured |
| `raw/<device>-<date>.csv` | Per-run telemetry at 1-minute intervals |
| `raw/<device>-<date>.md` | Run notes: ambient temperature, charger, case on/off, anything unusual |

## What we measure

Per [issue #4](../docs/MILESTONES.md#4-overnight-measurement-harness), sampled every minute across a full 8-hour overnight run:

- Decode tokens/sec — **sustained, not burst**
- Prefill tokens/sec
- Battery level, temperature, and charge current
- Thermal throttling status reported by the platform
- Estimated power draw in watts
- Interruption events, with causes

## The commitment

**We publish these results including when they are bad.**

If measured sustained throughput comes in at a quarter of the modelled figure, that goes in `DEVICES.md`, the model constants get corrected, the whitepaper gets revised, and the change is recorded in [Appendix B](../WHITEPAPER.md#appendix-b-what-we-retract) alongside the other retractions.

A project whose only real asset is trustworthy numbers does not get to be selective about which measurements it shows. The same applies to the [energy cost](../docs/threat-model.md#energy-cost-and-honesty) figures.

## Contributing a measurement

You do not need to be an engineer — you need an Android phone, a charger, and one night. Instructions will land here once the measurement harness ships. Track [issue #8](../docs/MILESTONES.md#8-help-wanted-benchmark-your-phone).

The model's weakest inputs, which your device directly tests:

- `THERMAL_DERATE` (0.70) — sustained vs burst over 8 hours
- `fp32_sustained_fraction` (0.30–0.33) — mobile GPU sustained floating-point, barely documented anywhere
