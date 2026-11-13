"""Strategy E: D + saturating reversion drift + optional pooled tails + inner scale."""
import math
from common import TAUS
from strategies2 import _emp_q, _interp, _rms, _HGRID

def forecast_E(case, win=1440, floor_out=0.5, rev_k=0.0, rev_gate=0.01,
               pooled_tails=False, inner_scale=1.0, sum_w=0.0):
    mkts = case['markets']
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
        drift = 0.0
        if rev_k and len(p) >= 61:
            d60 = p[-1] - p[-61]
            if abs(d60) > rev_gate:
                drift = -rev_k * d60  # full reversion amount, phased in by g(h)
        rows = []
        for h in range(1, 241):
            qs = [_interp(h, _HGRID, [q_by_h[j][t] for j in range(len(_HGRID))]) for t in range(5)]
            if pooled_tails:
                pt = [_interp(h, _HGRID, [pooled_q[H][t]*scale for H in _HGRID]) for t in range(5)]
                qs[0] = min(qs[0], pt[0])
                qs[4] = max(qs[4], pt[4])
            g = h / (h + 40.0)  # saturating phase-in of reversion
            med_shift = drift * g
            # inner quantiles shrink toward median; outer keep empirical/pooled width
            med_q = qs[2]
            row = [x + q + med_shift for q in qs]
            row[1] = row[2] + (row[1]-row[2]) * inner_scale
            row[3] = row[2] + (row[3]-row[2]) * inner_scale
            med = row[2]
            bw = 0.0025 * math.sqrt(h)
            if floor_out > 0:
                row[0] = min(row[0], med - floor_out * 1.644854 * bw)
                row[4] = max(row[4], med + floor_out * 1.644854 * bw)
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
