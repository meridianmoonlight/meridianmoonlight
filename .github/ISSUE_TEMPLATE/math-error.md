---
name: Math or assumption error
about: You think a number we published is wrong. This is the most valuable issue you can file.
title: "[math] "
labels: analysis
---

## Which number

Where does it appear? (`WHITEPAPER.md §X`, `analysis/NUMBERS.md`, the website, a figure)

Current published value:

## What you think it should be

Your value, and how you got there:

## Why

A source, a measurement, a derivation, or an argument. Any of those is useful — a hunch is worth filing too, just say that's what it is.

## Which constant

If it's an input to the model, which one in `analysis/compute_model.py`?

We already consider these our weakest, so you are not stepping on toes by challenging them:

- [ ] `THERMAL_DERATE` (0.70)
- [ ] `fp32_sustained_fraction` (0.30–0.33)
- [ ] `SHARE_RAM_8GB_PLUS` (0.26)
- [ ] `DC_TOKENS_PER_SEC_PER_GPU` (3000)
- [ ] Something else:
- [ ] Not an input — an error in the derivation itself

## Anything else

---

*Being corrected is the point. If you are right, this gets fixed and the change is recorded in Appendix B of the whitepaper with the rest of our retractions. You will be credited unless you would rather not be.*
