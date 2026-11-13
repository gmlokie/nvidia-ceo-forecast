import sys
sys.path.insert(0, 'backtest')
from common import load_case, score_case, house_baseline
import strategies4 as F

CASES = ['p00','p01','p02','p03','p04','p05','h00','h01','h02','h03','h04']
data = {cid: load_case(cid) for cid in CASES}
def ev(fn):
    res = {}
    for cid in CASES:
        case, ans = data[cid]
        res[cid] = score_case(fn(case), ans)[0]
    prac = sum(res[c] for c in CASES[:6])/6
    recent = sum(res[c] for c in ['p04','p05','h03','h04'])/4
    weighted = (2*recent + prac)/3
    return prac, recent, weighted, res

variants = [
    ('F rev0.3 inner0.8', dict()),
    ('F rev0.3 inner0.7', dict(inner_scale=0.7)),
    ('F rev0.3 inner0.9', dict(inner_scale=0.9)),
    ('F rev0.3 inner0.8 tails4320', dict(tails_win=4320)),
    ('F rev0.2 inner0.8', dict(rev_k=0.2)),
    ('F rev0.4 inner0.8', dict(rev_k=0.4)),
    ('F rev0.3 inner0.8 lookback120', dict(rev_lookback=120)),
    ('F rev0.3 inner0.8 tails4320 lookback120', dict(tails_win=4320, rev_lookback=120)),
    ('F rev0 inner0.8', dict(rev_k=0.0)),
]
for name, kw in variants:
    prac, recent, weighted, res = ev(lambda c, kw=kw: F.forecast_F(c, **kw))
    print(f"{name:38s} prac={prac:.4f} recent={recent:.4f} weighted={weighted:.4f} | " +
          " ".join(f"{c}={res[c]:.3f}" for c in ['p00','p01','p02','p03','p04','p05','h03','h04']))
