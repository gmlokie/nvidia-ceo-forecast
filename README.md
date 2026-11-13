# Forecast Polymarket's Next NVIDIA CEO Prices — make.fun entry

Competition: **polymarket-nvidia-ceo-forecast-01** ($250, deadline 14 Nov 2026 04:00 WIB).
Entry: `main.py` — a Python 3.13 program (stdlib only, offline, deterministic)
that reads one case `/input/<id>.in` and writes `/output/<id>.out`:
for every trading market of Polymarket's "Next CEO of NVIDIA?" event, five
quantiles (5%, 25%, 50%, 75%, 95%) of the Yes price at each of the 240
minutes after the checkpoint.

## Method

Prediction-market prices are jump-dominated, not Gaussian random walks:
in the reconstructed history, **88% of 1-minute price changes are exactly 0**,
while ~1.4% exceed 0.02 and single-minute jumps reach 0.48. The forecaster
is therefore built from **empirical h-step change distributions**:

1. Per market, take the last 24h of 1-minute prices. For horizons
   h ∈ {1, 2, 4, 8, 16, 32, 64, 128, 240} minutes, compute the empirical
   quantiles (5/25/50/75/95) of the h-step price changes, then interpolate
   each quantile in log(h). This gives tight inner bands (most minutes the
   price does not move) and fat outer tails (rare jumps).
2. Markets with <30 samples at a horizon fall back to the pooled
   cross-market change distribution, scaled by the market's own 1-minute RMS.
3. Inner (25%/75%) bands are shrunk 0.7× toward the median — the raw
   empirical inner quantiles are slightly too wide.
4. Median drift: after a >0.01 move in the last 60 minutes, expect partial
   mean reversion (−0.3× the move), phased in as h/(h+40). Measured on
   history: corr(60-min move before checkpoint, 240-min move after) = −0.40.

Things tested and **rejected** by backtest (see `transcripts/BUILD_LOG.md`):
sum-to-one coherence (the cross-market sum drifts ±0.1–0.3 over 4h), pooled
tails (imports big-market jumps into small markets), long-memory (72h) tails,
a hard volatility floor, and a 120-minute reversion lookback.

## Backtest (reconstructed from Polymarket CLOB history)

Pinball loss, percentage points. Practice = 6 official practice windows
(2026-11-12 06:00 → 2026-11-13 02:00 UTC); holdouts = 5 extra windows,
including 2 recent-regime ones (2026-11-13 06:00, 10:00 UTC).

| set | this entry | house baseline | official baseline* |
|---|---|---|---|
| practice mean (6 cases) | **0.359** | 0.371 | 0.3636 |
| recent regime (p04, p05, h03, h04) | **0.165** | 0.250 | — |
| holdout mean (5 cases) | **1.421** | 1.469 | — |

\* Official practice loss of the house baseline, from the competition rules.
My reconstruction reproduces it at 0.371 (2% off), so the cases are faithful.

Honest caveats: the entry beats the baseline clearly in the recent (quiet)
regime (−34%) but only modestly on the full practice set (−3%), and it
*loses* to the baseline on the three jump-dominated early windows
(p00, p02, h02 — Nov 11–12 price discovery, e.g. Colette Kress 0.05→0.41
in 4h). If a news jump lands inside a final window, that case will score
~0.5–0.6. No forecaster can predict the jump; tight bands are the right
expected-value play because jumps are rare. The house AI model's practice
loss is not published (the API shows "Best baseline 0.313", unconfirmed
whether that is the model), so beating it is not guaranteed — the entry
beats the published baseline, and its recent-regime score (0.165) is well
below 0.313.

## Running

```sh
python3 main.py                 # all *.in files in $MAKEFUN_INPUT_DIR (default /input)
python3 main.py p00 p01         # specific case ids
MAKEFUN_INPUT_DIR=./cases MAKEFUN_OUTPUT_DIR=./out python3 main.py
```

Runtime ~0.16 s/case on 1 CPU (limit 8 s). Deterministic: two runs on the
same case produce byte-identical output (verified). Output ≤ 239 KB per
case (limit 1,048,576 bytes); exactly one key `forecasts`, one row per
market (`{"id", "q"}`), `q` = 240 rows × 5 numbers, non-decreasing, in
[0, 1], rounded to 6 decimals.

## Layout

- `main.py` — the entry (stdlib only, no network).
- `backtest/` — harness, strategies tried, diagnostics, validation script.
- `cases/` — 11 reconstructed cases (`.in`) + answers (`.ans.json`) built
  from Polymarket Gamma + CLOB public APIs (`build_cases.py`,
  `fetch_history.py`, `event.json`, `universe.json`, `history_raw.json`).
- `transcripts/BUILD_LOG.md` — full build log: spec, submission-gate check,
  data reconstruction, every strategy tried with scores, adversarial review.

## License

MIT — see `LICENSE`. SPDX-License-Identifier: MIT.
