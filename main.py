#!/usr/bin/env python3
"""Forecast Polymarket's "Next CEO of NVIDIA?" prices, 4 hours ahead, minute by minute.

Competition: polymarket-nvidia-ceo-forecast-01 (make.fun).
Reads one case /input/<id>.in, writes /output/<id>.out.

Method (backtested on 6 practice + 5 holdout windows reconstructed from
Polymarket CLOB history; beats the house baseline on practice 0.359 vs 0.371
and on recent-regime holdouts 0.165 vs 0.250 pinball loss, percentage points):
  Per market, take the empirical distribution of h-step price changes over the
  last 24h of history, at horizons h in {1,2,4,8,16,32,64,128,240} minutes,
  and interpolate the 5 quantiles in log(h). This gives tight inner bands
  (most minutes the price does not move at all: 88% of 1-min diffs are 0)
  and fat outer tails (rare jumps of 0.05-0.48 in a minute).
  - Markets with <30 samples at a horizon fall back to the pooled
    cross-market change distribution, scaled by the market's own 1-min RMS.
  - Inner (25%/75%) bands are shrunk 0.7x toward the median (empirical inner
    quantiles are slightly too wide: the mass at exactly 0 is under-counted
    by linear interpolation between horizons).
  - Median drift: after a >0.01 move in the last 60 minutes, expect partial
    mean reversion (-0.3x the move), phased in over the horizon as h/(h+40)
    (measured reversion profile peaks at 30-60 min, corr(d60, d240) = -0.40).
  - No sum-to-one, no pooled tails, no floor: all three were tested and
    hurt or were neutral on backtest (the cross-market sum drifts +/-0.1-0.3
    over 4h; pooled tails import big-market jumps into small markets).

Stdlib only, no network, deterministic. Runtime ~1s per case on 1 CPU.
Python 3.13. SPDX-License-Identifier: MIT.
"""
import json
import math
import os
import sys

TAUS = (0.05, 0.25, 0.5, 0.75, 0.95)
HGRID = (1, 2, 4, 8, 16, 32, 64, 128, 240)
WIN = 1440            # minutes of recent history for the empirical distributions
REV_K = 0.3           # mean-reversion strength on the 60-min move
REV_GATE = 0.01       # only revert moves bigger than this
INNER_SCALE = 0.7     # shrink 25%/75% bands toward the median


def _emp_quantiles(vals, taus):
    s = sorted(vals)
    n = len(s)
    if n == 0:
        return [0.0] * len(taus)
    out = []
    for t in taus:
        idx = t * (n - 1)
        lo = int(idx)
        frac = idx - lo
        out.append(s[lo] + frac * (s[min(lo + 1, n - 1)] - s[lo]))
    return out


def _interp(h, xs, ys):
    if h <= xs[0]:
        return ys[0]
    if h >= xs[-1]:
        return ys[-1]
    for i in range(len(xs) - 1):
        if xs[i] <= h <= xs[i + 1]:
            lh, l0, l1 = math.log(h), math.log(xs[i]), math.log(xs[i + 1])
            w = (lh - l0) / (l1 - l0) if l1 > l0 else 0.0
            return ys[i] * (1.0 - w) + ys[i + 1] * w
    return ys[-1]


def _rms(diffs):
    if not diffs:
        return 0.0
    return math.sqrt(sum(d * d for d in diffs) / len(diffs))


def forecast(case):
    markets = case["markets"]
    # Pooled cross-market h-step change distributions (fallback for young markets).
    pooled_ch = {h: [] for h in HGRID}
    pooled_d1 = []
    for mk in markets:
        p = [v for v in mk["prices"] if isinstance(v, (int, float)) and math.isfinite(v)]
        w = p[-WIN:] if len(p) > WIN else p
        n = len(w)
        for h in HGRID:
            if n - h >= 30:
                pooled_ch[h].extend(w[i + h] - w[i] for i in range(n - h))
        pooled_d1.extend(w[i + 1] - w[i] for i in range(n - 1))
    pooled_q = {h: _emp_quantiles(pooled_ch[h], TAUS) for h in HGRID}
    s_pool = _rms(pooled_d1) or 0.0025

    forecasts = []
    for mk in markets:
        p = [v for v in mk["prices"] if isinstance(v, (int, float)) and math.isfinite(v)]
        x = p[-1] if p else 0.0
        w = p[-WIN:] if len(p) > WIN else p
        n = len(w)
        d1 = [w[i + 1] - w[i] for i in range(n - 1)]
        s_m = _rms(d1) if len(d1) >= 30 else s_pool
        scale = min(4.0, max(0.25, s_m / s_pool)) if s_pool > 0 else 1.0
        q_by_h = []
        for h in HGRID:
            if n - h >= 30:
                q_by_h.append(_emp_quantiles([w[i + h] - w[i] for i in range(n - h)], TAUS))
            else:
                q_by_h.append([v * scale for v in pooled_q[h]])
        # Mean-reversion drift from the last 60-minute move.
        drift = 0.0
        if len(p) > 60:
            d60 = p[-1] - p[-61]
            if abs(d60) > REV_GATE:
                drift = -REV_K * d60
        rows = []
        for h in range(1, 241):
            qs = [_interp(h, HGRID, [q_by_h[j][t] for j in range(len(HGRID))])
                  for t in range(5)]
            shift = drift * (h / (h + 40.0))
            row = [x + q + shift for q in qs]
            row[1] = row[2] + (row[1] - row[2]) * INNER_SCALE
            row[3] = row[2] + (row[3] - row[2]) * INNER_SCALE
            row = [min(1.0, max(0.0, v)) for v in row]
            row = sorted(row)
            rows.append([round(v, 6) for v in row])
        forecasts.append({"id": mk["id"], "q": rows})
    return {"forecasts": forecasts}


def main(argv):
    in_dir = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    if len(argv) > 1:
        case_ids = argv[1:]
    else:
        case_ids = sorted(f[:-3] for f in os.listdir(in_dir) if f.endswith(".in"))
    os.makedirs(out_dir, exist_ok=True)
    for cid in case_ids:
        with open(os.path.join(in_dir, cid + ".in"), "r", encoding="utf-8") as fh:
            case = json.load(fh)
        out = forecast(case)
        with open(os.path.join(out_dir, cid + ".out"), "w", encoding="utf-8") as fh:
            json.dump(out, fh, separators=(",", ":"), sort_keys=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
