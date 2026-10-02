#!/usr/bin/env python3
"""Scenario checks behind the statements in Section 7 of the paper:

  * the naive shift error persists, and is no smaller, when every platform
    shares one unbiased symmetric measurement function, so it is a scale
    effect rather than a cost of non-equivalence;
  * wrong-sign days all but vanish in that case, and grow with the spread
    between the platforms' measurement functions;
  * the wrong-sign count depends on where latent sentiment sits relative to
    the platforms' net bias (pre-event baseline).

Every scenario uses the same 500 seeds as the published run.

    python sensitivity.py
"""
import numpy as np
import simulation_study as S

SEED, REPS = 20261201, 500

SCENARIOS = [
    ("published configuration",              S.PLATFORMS,                S.BASELINE),
    ("homogeneous (one unbiased function)",  S.homogeneous(S.PLATFORMS), S.BASELINE),
    ("heterogeneity x0.25",                  S.scaled(S.PLATFORMS, 0.25), S.BASELINE),
    ("heterogeneity x0.5",                   S.scaled(S.PLATFORMS, 0.5),  S.BASELINE),
    ("heterogeneity x1.5",                   S.scaled(S.PLATFORMS, 1.5),  S.BASELINE),
    ("baseline -0.1",                        S.PLATFORMS,                -0.1),
    ("baseline 0.3",                         S.PLATFORMS,                 0.3),
]

if __name__ == "__main__":
    print(f"{'scenario':38s} {'naive shift err':>16s} {'adj shift err':>14s} "
          f"{'naive wrong-sign days':>24s} {'adj wrong-sign days':>22s}")
    for label, platforms, baseline in SCENARIOS:
        r = S.replicate(SEED, REPS, platforms, baseline)
        fn, fa = r["flips_naive"], r["flips_adjusted"]
        print(f"{label:38s} {r['naive_bias'].mean():+16.3f} {r['adjusted_bias'].mean():+14.4f} "
              f"{fn.mean():12.1f} [{S.ci(fn)[0]:.0f}, {S.ci(fn)[1]:.0f}]{'':>3s}"
              f"{fa.mean():10.1f} [{S.ci(fa)[0]:.0f}, {S.ci(fa)[1]:.0f}]")
