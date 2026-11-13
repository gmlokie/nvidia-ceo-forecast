"""Debug C vs baseline per-tau; test D variants (reversion + pooled fallback + tail scale)."""
import sys, math
sys.path.insert(0, 'backtest')
from common import load_case, score_case, house_baseline, TAUS, pinball
import strategies as S

def loss_by_tau(fc, ans):
    by = {t: [0.0, 0] for t in TAUS}
    for mid, rows in fc.items():
        for h in range(240):
            y = ans[mid][h]
            for t, q in zip(TAUS, rows[h]):
                by[t][0] += pinball(y, q, t); by[t][1] += 1
    return {t: 100*v[0]/v[1] for t, v in by.items()}

for cid in ['p03', 'p05']:
    case, ans = load_case(cid)
    for name, fc in [('BASE', house_baseline(case)), ('C1440', S.forecast_C(case, win=1440))]:
        print(cid, name, {t: round(v, 3) for t, v in loss_by_tau(fc, ans).items()}, 'total', round(score_case(fc, ans)[0], 4))
    # young-market check: Tim Cook history length in p03
    for mk in case['markets']:
        if mk['name'] in ('Tim Cook', 'Curtis Priem'):
            print(f"   {mk['name']}: history len={len(mk['prices'])}")
