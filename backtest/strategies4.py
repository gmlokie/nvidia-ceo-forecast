"""Strategy F: E + long-memory tails (4320) + tunable inner scale + reversion source."""
import math
from common import TAUS
from strategies2 import _emp_q, _interp, _rms, _HGRID

def forecast_F(case, win=1440, tails_win=1440, rev_k=0.3, rev_gate=0.01,
               rev_lookback=60, inner_scale=0.8):
    mkts = case['markets']
    ids = [mk['id'] for mk in mkts]
    out = {}
    for mk in mkts:
        p = mk['prices']; x = p[-1]
        def q_by_h_for(win_):
            w = p[-win_:] if len(p) > win_ else p
            n = len(w)
            res = []
            for H in _HGRID:
                if n - H >= 30:
                    res.append(_emp_q([w[i+H]-w[i] for i in range(n-H)], TAUS))
                else:
                    res.append(None)
            return res, w
        q_c, w_c = q_by_h_for(win)
        q_t, w_t = q_by_h_for(tails_win)
        # fill missing (short history) with available horizon's values, else 0
        for arr in (q_c, q_t):
            last = [0.0]*5
            for j in range(len(_HGRID)):
                if arr[j] is None:
                    arr[j] = last
                else:
                    last = arr[j]
        drift = 0.0
        if rev_k and len(p) > rev_lookback:
            d = p[-1] - p[-1-rev_lookback]
            if abs(d) > rev_gate:
                drift = -rev_k * d
        rows = []
        for h in range(1, 241):
            qc = [_interp(h, _HGRID, [q_c[j][t] for j in range(len(_HGRID))]) for t in range(5)]
            qt = [_interp(h, _HGRID, [q_t[j][t] for j in range(len(_HGRID))]) for t in range(5)]
            qs = [qc[0], qc[1], qc[2], qc[3], qc[4]]
            qs[0] = min(qc[0], qt[0])  # wider lower tail from long memory
            qs[4] = max(qc[4], qt[4])  # wider upper tail from long memory
            g = h / (h + 40.0)
            med_shift = drift * g
            row = [x + q + med_shift for q in qs]
            row[1] = row[2] + (row[1]-row[2]) * inner_scale
            row[3] = row[2] + (row[3]-row[2]) * inner_scale
            row = [min(1.0, max(0.0, v)) for v in row]
            row = sorted(row)
            rows.append([round(v, 6) for v in row])
        out[mk['id']] = rows
    return out
