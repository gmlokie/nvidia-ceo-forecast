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

print("BASELINE prac=0.3710 recent=%.4f" % ev(lambda c: house_baseline(c))[1])
variants = [
    ('E base', dict()),
    ('E rev0.3', dict(rev_k=0.3)),
    ('E rev0.5', dict(rev_k=0.5)),
    ('E rev0.3 pooled_tails', dict(rev_k=0.3, pooled_tails=True)),
    ('E rev0.3 inner0.8', dict(rev_k=0.3, inner_scale=0.8)),
    ('E rev0.3 pooled inner0.8', dict(rev_k=0.3, pooled_tails=True, inner_scale=0.8)),
    ('E rev0.3 floor0', dict(rev_k=0.3, floor_out=0.0)),
    ('E rev0.3 floor0 pooled', dict(rev_k=0.3, floor_out=0.0, pooled_tails=True)),
    ('E rev0.3 win4320', dict(rev_k=0.3, win=4320)),
    ('E rev0.3 sum0.5', dict(rev_k=0.3, sum_w=0.5)),
    ('E rev0.3 pooled inner0.8 sum0.5', dict(rev_k=0.3, pooled_tails=True, inner_scale=0.8, sum_w=0.5)),
    ('E rev0.5 pooled inner0.8', dict(rev_k=0.5, pooled_tails=True, inner_scale=0.8)),
]
for name, kw in variants:
    prac, recent, weighted, res = ev(lambda c, kw=kw: E.forecast_E(c, **kw))
    print(f"{name:32s} prac={prac:.4f} recent={recent:.4f} weighted={weighted:.4f} | " +
          " ".join(f"{c}={res[c]:.3f}" for c in ['p00','p01','p02','p03','p04','p05','h03','h04']))
