import sys
sys.path.insert(0, 'backtest')
from common import load_case, score_case, house_baseline
import strategies3 as E

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

for name, kw in [
    ('E floor0.5 rev0.3 inner0.8', dict(floor_out=0.5, rev_k=0.3, inner_scale=0.8)),
    ('E floor0 rev0.3 inner0.8', dict(floor_out=0.0, rev_k=0.3, inner_scale=0.8)),
    ('E floor0.5 rev0.3 inner0.7', dict(floor_out=0.5, rev_k=0.3, inner_scale=0.7)),
    ('E floor0 rev0.3 inner0.7', dict(floor_out=0.0, rev_k=0.3, inner_scale=0.7)),
    ('E floor0.5 rev0.3 inner0.8 win720', dict(floor_out=0.5, rev_k=0.3, inner_scale=0.8, win=720)),
    ('E floor0.5 rev0.3 inner0.8 win2880', dict(floor_out=0.5, rev_k=0.3, inner_scale=0.8, win=2880)),
]:
    prac, recent, weighted, res = ev(lambda c, kw=kw: E.forecast_E(c, **kw))
    print(f"{name:36s} prac={prac:.4f} recent={recent:.4f} weighted={weighted:.4f} | " +
          " ".join(f"{c}={res[c]:.3f}" for c in ['p00','p01','p02','p03','p04','p05','h00','h01','h02','h03','h04']))
