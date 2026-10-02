#!/usr/bin/env python3
"""Simulation study of Section 7: the cost of assuming cross-platform
measurement equivalence, with known ground truth. Needs no collected data.

The generating parameters below are the fixed values used for every result
reported in the paper. They were fixed before any replication was run and
illustrate the mechanism; they are not calibrated to any corpus.

Design. A latent daily sentiment series theta_t (common truth) reacts to an
anchor event with a known negative shift and recovers gradually. Four
platforms observe theta_t through platform-specific measurement: each post
expresses y = theta + affordance bias + noise, discretised by
platform-specific thresholds into negative / neutral / positive. Platform
volume shares also drift over time. Two indices are computed daily:

  NAIVE     the pooled mean of coded values across platforms;
  ADJUSTED  each platform's latent value estimated by inverting that
            platform's known measurement function, pooled with daily
            volume weights.

The adjusted index uses the TRUE measurement functions (an oracle); in an
application those functions would be estimated, and estimation error would
cost the adjusted index some of its advantage.

Reproduce the paper (Section 7 and Figure 1):

    python simulation_study.py --seed 20261201 --replications 500

Other scenarios used in Section 7 are run by sensitivity.py.
"""
import argparse
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Labels are mnemonic only; these constructed measurement functions
# assert nothing about the real platforms.
PLATFORMS = {
    #            bias   thr_lo  thr_hi  base_n  drift(per day)
    "twitter":  (-0.15, -0.20,  0.25,   3000,   -8.0),   # negative-leaning, loses share
    "reddit":   (-0.05, -0.35,  0.35,   1200,   +2.0),
    "youtube":  (+0.10, -0.30,  0.20,    900,   +1.0),   # positive-leaning thresholds
    "quora":    (+0.20, -0.10,  0.45,    150,    0.0),   # strongly positive-leaning, tiny
}
DAYS = 60
EVENT_DAY = 30
EVENT_SHIFT = -0.5   # true latent shift at the event
NOISE_SD = 0.6
BASELINE = 0.1       # pre-event latent sentiment


def homogeneous(platforms):
    """Every platform shares one unbiased, symmetric measurement function;
    volumes and drift are unchanged."""
    return {p: (0.0, -0.3, 0.3, n, d) for p, (_, _, _, n, d) in platforms.items()}


def scaled(platforms, k):
    """Scale the spread between platforms' measurement functions by k
    (k = 0 gives the homogeneous case, k = 1 the published one)."""
    return {p: (b * k, -0.3 + (lo + 0.3) * k, 0.3 + (hi - 0.3) * k, n, d)
            for p, (b, lo, hi, n, d) in platforms.items()}


def code(y, lo, hi):
    return np.where(y < lo, -1, np.where(y > hi, 1, 0))


def inversion_curve(bias, lo, hi, rng, grid_n=301, draws=6000):
    """Expected coded value as a function of the latent value, for one
    platform's known measurement function. Computed once per platform."""
    grid = np.linspace(-1.5, 1.5, grid_n)
    eps = rng.normal(0, NOISE_SD, draws)
    expect = np.array([code(g + bias + eps, lo, hi).mean() for g in grid])
    return grid, expect


def inversion_curves(platforms):
    crng = np.random.default_rng(12345)
    return {p: inversion_curve(b, lo, hi, crng)
            for p, (b, lo, hi, _, _) in platforms.items()}


def shift(series):
    """Event shift: mean of the ten days after the event minus the ten before."""
    return series[EVENT_DAY:EVENT_DAY + 10].mean() - series[EVENT_DAY - 10:EVENT_DAY].mean()


def run(seed, curves=None, platforms=None, baseline=BASELINE):
    platforms = PLATFORMS if platforms is None else platforms
    rng = np.random.default_rng(seed)
    theta = baseline * np.ones(DAYS)
    theta[EVENT_DAY:] += EVENT_SHIFT * np.exp(-np.arange(DAYS - EVENT_DAY) / 10.0)
    if curves is None:
        curves = inversion_curves(platforms)

    naive_num = np.zeros(DAYS); naive_den = np.zeros(DAYS)
    adj_est = np.zeros((len(platforms), DAYS)); adj_w = np.zeros((len(platforms), DAYS))
    for k, (p, (bias, lo, hi, n0, drift)) in enumerate(platforms.items()):
        grid, expect = curves[p]
        for t in range(DAYS):
            n = max(30, int(n0 + drift * t))
            y = theta[t] + bias + rng.normal(0, NOISE_SD, n)
            c = code(y, lo, hi)
            naive_num[t] += c.sum(); naive_den[t] += n
            adj_est[k, t] = grid[np.abs(expect - c.mean()).argmin()]
            adj_w[k, t] = n
    naive = naive_num / naive_den
    adjusted = (adj_est * adj_w).sum(0) / adj_w.sum(0)

    flips_naive = int(((naive > 0) != (theta > 0)).sum())
    flips_adj = int(((adjusted > 0) != (theta > 0)).sum())
    return dict(theta=theta, naive=naive, adjusted=adjusted,
                true_shift=shift(theta), naive_shift=shift(naive),
                adjusted_shift=shift(adjusted),
                flips_naive=flips_naive, flips_adjusted=flips_adj)


def replicate(base_seed, reps, platforms=None, baseline=BASELINE):
    platforms = PLATFORMS if platforms is None else platforms
    curves = inversion_curves(platforms)
    out = [run(base_seed + r, curves, platforms, baseline) for r in range(reps)]
    return dict(
        true_shift=out[-1]["true_shift"],
        naive_bias=np.array([o["naive_shift"] - o["true_shift"] for o in out]),
        adjusted_bias=np.array([o["adjusted_shift"] - o["true_shift"] for o in out]),
        flips_naive=np.array([o["flips_naive"] for o in out]),
        flips_adjusted=np.array([o["flips_adjusted"] for o in out]),
    )


def ci(x):
    return np.percentile(x, [2.5, 97.5])


def report(base_seed, reps):
    r = replicate(base_seed, reps)
    nb, ab, fn, fa = r["naive_bias"], r["adjusted_bias"], r["flips_naive"], r["flips_adjusted"]
    print(f"replications             : {reps} (seeds {base_seed} to {base_seed + reps - 1})")
    print(f"true event shift         : {r['true_shift']:+.3f}")
    print(f"naive shift bias         : mean {nb.mean():+.4f}  95% [{ci(nb)[0]:+.4f}, {ci(nb)[1]:+.4f}]")
    print(f"adjusted shift bias      : mean {ab.mean():+.4f}  95% [{ci(ab)[0]:+.4f}, {ci(ab)[1]:+.4f}]")
    print(f"naive wrong-sign days    : mean {fn.mean():.1f} of {DAYS}  95% [{ci(fn)[0]:.0f}, {ci(fn)[1]:.0f}]")
    print(f"adjusted wrong-sign days : mean {fa.mean():.1f} of {DAYS}  95% [{ci(fa)[0]:.0f}, {ci(fa)[1]:.0f}]")


def plot(seed, outfile="fig_simulation_demo.png"):
    r = run(seed)
    print(f"single run seed {seed}: true {r['true_shift']:+.3f}, naive {r['naive_shift']:+.3f}, "
          f"adjusted {r['adjusted_shift']:+.3f}, wrong-sign days naive {r['flips_naive']}, "
          f"adjusted {r['flips_adjusted']}")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(r["theta"], color="black", label="Latent truth")
    ax.plot(r["naive"], color="#d62728", label="Naive pooled index")
    ax.plot(r["adjusted"], color="#1f77b4", label="Measurement-adjusted index")
    ax.axvline(EVENT_DAY, color="grey", linestyle=":", linewidth=1)
    ax.set_xlabel("Day"); ax.set_ylabel("Sentiment"); ax.legend(frameon=False)
    ax.set_title("Simulated cost of assuming equivalence")
    fig.tight_layout(); fig.savefig(outfile, dpi=200)
    print(f"figure: {outfile}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--seed", type=int, default=20261201)
    ap.add_argument("--replications", type=int, default=0,
                    help="number of replications (seeds seed, seed+1, ...); 0 skips them")
    a = ap.parse_args()
    if a.replications:
        report(a.seed, a.replications)
    plot(a.seed)
