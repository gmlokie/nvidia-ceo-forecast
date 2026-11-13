"""Candidate forecasters A (logit/RMS vol), B (A + sum-to-one), C (empirical change quantiles)."""
import math
from common import TAUS, Z

def _clip(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v

def _round6(v):
    return round(v, 6)

def _rms(diffs):
    if not diffs:
        return 0.0
    return math.sqrt(sum(d * d for d in diffs) / len(diffs))

def _median(v):
    s = sorted(v); n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])

# ---------------- Strategy A: price-space RMS-vol random walk + jump-reversion drift ----
def forecast_A(case, vol_win=720, sigma_floor=0.0012, sigma_cap=0.02, revert=0.0):
    out = {}
    for mk in case['markets']:
        p = mk['prices']; x = p[-1]
        w = p[-vol_win:] if len(p) > vol_win else p
        diffs = [w[i+1] - w[i] for i in range(len(w)-1)]
        sig = min(sigma_cap, max(sigma_floor, _rms(diffs)))
        # jump-reversion drift: if last 60-min move is big, expect partial reversion
        drift = 0.0
        if revert and len(p) >= 61:
            d60 = p[-1] - p[-61]
            if abs(d60) > 0.03:
                drift = -revert * d60 / 240.0  # per-minute drift, decays over horizon
        rows = []
        for h in range(1, 241):
            med = x + drift * h
            s = sig * math.sqrt(h)
            row = [_clip(med + z * s) for z in Z]
            rows.append([_round6(v) for v in row])
        out[mk['id']] = rows
    return out

# ---------------- Strategy B: A + sum-to-one coherence (weight w) ----------------
def forecast_B(case, sum_w=0.5, **kw):
    fc = forecast_A(case, **kw)
    ids = [mk['id'] for mk in case['markets']]
    s0 = sum(case['markets'][i]['prices'][-1] for i in range(len(ids)))
    out = {}
    for h in range(240):
        sh = sum(fc[mid][h][2] for mid in ids)
        f = (s0 / sh) ** sum_w if sh > 0 else 1.0
        for mid in ids:
            med = fc[mid][h][2]
            row = [med + (q - med) * f for q in fc[mid][h]]
            row = [_clip(v) for v in row]
            row = sorted(row)
            out.setdefault(mid, []).append([_round6(v) for v in row])
    return out

# ---------------- Strategy C: empirical h-step change quantiles ----------------
_HGRID = [1, 2, 4, 8, 16, 32, 64, 128, 240]

def _emp_quantiles(vals, taus):
    s = sorted(vals); n = len(s)
    res = []
    for t in taus:
        idx = t * (n - 1)
        lo = int(idx); frac = idx - lo
        res.append(s[lo] + frac * (s[min(lo+1, n-1)] - s[lo]))
    return res

def _interp(h, xs, ys):
    if h <= xs[0]:
        return ys[0]
    if h >= xs[-1]:
        return ys[-1]
    for i in range(len(xs)-1):
        if xs[i] <= h <= xs[i+1]:
            lh, l0, l1 = math.log(h), math.log(xs[i]), math.log(xs[i+1])
            w = (lh - l0) / (l1 - l0) if l1 > l0 else 0.0
            return ys[i] * (1-w) + ys[i+1] * w
    return ys[-1]

def forecast_C(case, win=1440, sum_w=0.0):
    per_market = {}
    for mk in case['markets']:
        p = mk['prices']; x = p[-1]
        w = p[-win:] if len(p) > win else p
        n = len(w)
        # empirical quantiles of h-step changes for each grid horizon
        q_by_h = []
        for H in _HGRID:
            if n - H < 20:
                q_by_h.append([0.0]*5)
                continue
            ch = [w[i+H] - w[i] for i in range(n - H)]
            q_by_h.append(_emp_quantiles(ch, TAUS))
        per_market[mk['id']] = (x, q_by_h)
    ids = [mk['id'] for mk in case['markets']]
    s0 = sum(case['markets'][i]['prices'][-1] for i in range(len(ids)))
    out = {}
    for mid in ids:
        x, q_by_h = per_market[mid]
        rows = []
        for h in range(1, 241):
            qs = [_interp(h, _HGRID, [q_by_h[j][t] for j in range(len(_HGRID))]) for t in range(5)]
            med = x + qs[2]
            row = [_clip(x + q) for q in qs]
            row = sorted(row)
            rows.append(row)
        out[mid] = rows
    if sum_w:
        # renormalize medians toward constant sum, scale widths
        for h in range(240):
            sh = sum(out[mid][h][2] for mid in ids)
            f = (s0 / sh) ** sum_w if sh > 0 else 1.0
            for mid in ids:
                med = out[mid][h][2]
                row = sorted(_clip(med + (q - med) * f) for q in out[mid][h])
                out[mid][h] = row
    return {mid: [[_round6(v) for v in row] for row in rows] for mid, rows in out.items()}
