# Is the Platform Part of the Measurement?

Code and materials for the simulation study (Section 7 and Figure 1) of the paper
*Is the Platform Part of the Measurement? A Protocol and Simulation Study for
Cross-Platform Equivalence of Machine-Labelled Policy Sentiment* (2026; arXiv link
to be added on posting).

The simulation has a known ground truth and needs no collected data. A latent daily
sentiment series reacts to an event; four platforms observe it through different
measurement functions (an affordance bias plus platform-specific thresholds that
discretise expression into negative, neutral and positive), and their volume shares
drift over time. Two daily indices are compared with the truth:

- **naive**: the pooled mean of coded values across platforms;
- **adjusted**: each platform's latent value recovered by inverting that platform's
  measurement function, pooled with volume weights. The adjusted index uses the
  *true* measurement functions; in an application they would be estimated.

## Reproduce the paper

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python simulation_study.py --seed 20261201 --replications 500
python sensitivity.py
```

`simulation_study.py` prints (in a few seconds):

```
replications             : 500 (seeds 20261201 to 20261700)
true event shift         : -0.332
naive shift bias         : mean -0.0420  95% [-0.0506, -0.0321]
adjusted shift bias      : mean +0.0013  95% [-0.0072, +0.0107]
naive wrong-sign days    : mean 13.8 of 60  95% [11, 17]
adjusted wrong-sign days : mean 0.8 of 60  95% [0, 2]
single run seed 20261201: true -0.332, naive -0.369, adjusted -0.326, wrong-sign days naive 13, adjusted 0
figure: fig_simulation_demo.png
```

and writes Figure 1 of the paper as `fig_simulation_demo.png`.

`sensitivity.py` runs the same 500 seeds under the scenarios that Section 7 describes:

| Scenario | Naive shift error | Naive wrong-sign days | Adjusted wrong-sign days |
|---|---|---|---|
| Published configuration | -0.042 | 13.8 [11, 17] | 0.8 [0, 2] |
| All platforms share one unbiased, symmetric function | -0.050 | 0.8 [0, 2] | 0.8 [0, 2] |
| Spread between platforms x0.25 | -0.050 | 1.8 [0, 3] | 0.9 [0, 2] |
| Spread between platforms x0.5 | -0.049 | 4.5 [3, 6] | 0.8 [0, 2] |
| Spread between platforms x1.5 | -0.029 | 42.9 [42, 43] | 0.8 [0, 2] |
| Pre-event baseline -0.1 (published: 0.1) | -0.003 | 0.0 [0, 0] | 0.0 [0, 0] |
| Pre-event baseline 0.3 | -0.052 | 2.7 [2, 4] | 0.2 [0, 1] |

Two readings follow, as stated in the paper. The naive shift error comes mainly from
treating the three-point coded scale as if it were the latent scale: it is no smaller
when every platform measures identically, so it is not a cost of non-equivalence.
The wrong-sign days are: they all but vanish when platforms measure identically, grow
with the spread between platforms, and depend on where latent sentiment sits
relative to the platforms' net bias. These are properties of the simulated
configuration, not bounds.

## Files

| File | Contents |
|---|---|
| `simulation_study.py` | Generating parameters, both indices, the 500-replication summary and Figure 1 |
| `sensitivity.py` | The scenario runs in the table above |
| `anchor_events.csv` | The fifteen UK fiscal policy anchor events of Table 2, fixed on 21 August 2026 before any window count was computed |
| `keyword_scheme.json` | The collection keyword scheme of the paper's appendix (topics, priority order, negation rule, gazetteer) |

The anchor-density audit uses two windows per event (48 hours and two weeks) and
inclusion thresholds of 50 and 200 comments per platform-event cell respectively.

## Not included

No social media data. The dissertation-stage corpus is not redistributed: its
identifiers were hashed at collection, so neither post text nor rehydratable
identifiers can be released. Annotation guidelines and aggregated per-event
statistics will be added with the empirical application.

## Licence

MIT, see `LICENSE`.
