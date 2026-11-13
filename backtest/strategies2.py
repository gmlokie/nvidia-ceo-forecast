"""Strategy D: empirical change quantiles + pooled fallback + outer floor + reversion median."""
import math
from common import TAUS, Z

_HGRID = [1, 2, 4, 8, 16, 32, 64, 128, 240]

def _emp_q(vals, taus):
    s = sorted(vals); n = len(s)
    if n == 0: return [0.0]*len(taus)
    res = []
    for t in taus:
        idx = t * (n - 1); lo = int(idx); frac = idx - lo
        res.append(s[lo] + frac * (s[min(lo+1, n-1)] - s[lo]))
    return res

def _interp(h, xs, ys):
    if h <= xs[0]: return ys[0]
    if h >= xs[-1]: return ys[-1]
    for i in range(len(xs)-1):
        if xs[i] <= h <= xs[i+1]:
            lh, l0, l1 = math.log(h), math.log(xs[i]), math.log(xs[i+1])
            w = (lh - l0) / (l1 - l0) if l1 > l0 else 0.0
            return ys[i]*(1-w) + ys[i+1]*w
    return ys[-1]

def _rms(d):
    return math.sqrt(sum(v*v for v in d)/len(d)) if d else 0.0

def forecast_D(case, win=1440, floor_out=0.5, rev_k=0.3, rev_gate=0.02, sum_w=0.0):
    mkts = case['markets']
    # pooled changes + pooled RMS (1-min diffs across markets)
    pooled_ch = {H: [] for H in _HGRID}
    pooled_d1 = []
    for mk in mkts:
        p = mk['prices']; w = p[-win:] if len(p) > win else p
        n = len(w)
        for H in _HGRID:
            if n - H >= 30:
                pooled_ch[H] += [w[i+H]-w[i] for i in range(n-H)]
        pooled_d1 += [w[i+1]-w[i] for i in range(n-1)]
    pooled_q = {H: _emp_q(pooled_ch[H], TAUS) for H in _HGRID}
    s_pool = _rms(pooled_d1) or 0.0025
    ids = [mk['id'] for mk in mkts]
    s0 = sum(mk['prices'][-1] for mk in mkts)
    out = {}
    for mk in mkts:
        p = mk['prices']; x = p[-1]
        w = p[-win:] if len(p) > win else p
        n = len(w)
        d1 = [w[i+1]-w[i] for i in range(n-1)]
        s_m = _rms(d1) if len(d1) >= 30 else s_pool
        scale = min(4.0, max(0.25, s_m / s_pool)) if s_pool > 0 else 1.0
        q_by_h = []
        for H in _HGRID:
            if n - H >= 30:
                q_by_h.append(_emp_q([w[i+H]-w[i] for i in range(n-H)], TAUS))
            else:
                q_by_h.append([v*scale for v in pooled_q[H]])
        # reversion drift from 60-min move
        drift_rate = 0.0
        if rev_k and len(p) >= 61:
            d60 = p[-1] - p[-61]
            if abs(d60) > rev_gate:
                drift_rate = -rev_k * d60 / 240.0
        rows = []
        for h in range(1, 241):
            qs = [_interp(h, _HGRID, [q_by_h[j][t] for j in range(len(_HGRID))]) for t in range(5)]
            row = [x + q + drift_rate*h for q in qs]
            # outer floor vs baseline half-width (relative to shifted median)
            med = row[2]
            bw = 0.0025 * math.sqrt(h)
            fl05 = med - floor_out * 1.644854 * bw
            fl95 = med + floor_out * 1.644854 * bw
            row[0] = min(row[0], fl05) if floor_out > 0 else row[0]
            row[4] = max(row[4], fl95) if floor_out > 0 else row[4]
            row = [min(1.0, max(0.0, v)) for v in row]
            row = sorted(row)
            rows.append([round(v, 6) for v in row])
        out[mk['id']] = rows
    if sum_w:
        for h in range(240):
            sh = sum(out[mid][h][2] for mid in ids)
            f = (s0/sh)**sum_w if sh > 0 else 1.0
            for mid in ids:
                med = out[mid][h][2]
                row = sorted(min(1.0, max(0.0, med + (q-med)*f)) for q in out[mid][h])
                out[mid][h] = [round(v, 6) for v in row]
    return out
