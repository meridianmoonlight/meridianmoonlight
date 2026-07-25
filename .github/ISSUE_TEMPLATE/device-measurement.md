---
name: Device measurement
about: Report measured throughput, power, or thermals from a real phone
title: "[measurement] "
labels: measurement
---

*You do not need to be an engineer to file this. A phone, a charger, and one night is the whole requirement.*

## Device

- Model:
- SoC:
- RAM:
- OS version:
- Case on during the run?
- Approximate ambient temperature:

## Model run

- Model and quantisation (e.g. `qwen2.5-1.5b-instruct-q4_k_m`):
- Runtime and version (llama.cpp commit, or MLC-LLM version):

## Measurements

| | Value |
|---|---|
| Decode tok/s, burst (first ~30s) | |
| Decode tok/s, sustained (hour 4+) | |
| Prefill tok/s | |
| Peak battery temperature | |
| Thermal throttling observed? | |
| Estimated watts during load | |
| Battery level start → end | |
| Interruptions, and why | |

## Raw data

Attach the CSV if you have one, or paste a sample.

## Notes

Anything surprising. **Bad results are as valuable as good ones** — if your phone throttled hard at hour two, that is exactly what we need to know and it will be published.
