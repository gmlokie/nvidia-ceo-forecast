"""Run all strategies on practice (p00-p05) + holdout (h00-h04) cases."""
import sys, time
sys.path.insert(0, 'backtest')
from common import load_case, score_case, house_baseline
import strategies as S

CASES = ['p00','p01','p02','p03','p04','p05','h00','h01','h02','h03','h04']
STRATS = [
    ('BASELINE', lambda c: house_baseline(c)),
    ('A vol720', lambda c: S.forecast_A(c)),
    ('A vol720 rev0.3', lambda c: S.forecast_A(c, revert=0.3)),
    ('A vol180', lambda c: S.forecast_A(c, vol_win=180)),
    ('B sum0.5', lambda c: S.forecast_B(c, sum_w=0.5)),
    ('B sum1.0', lambda c: S.forecast_B(c, sum_w=1.0)),
    ('C win1440', lambda c: S.forecast_C(c, win=1440)),
    ('C win4320', lambda c: S.forecast_C(c, win=4320)),
    ('C win1440 sum0.5', lambda c: S.forecast_C(c, win=1440, sum_w=0.5)),
    ('C win4320 sum0.5', lambda c: S.forecast_C(c, win=4320, sum_w=0.5)),
]
data = {cid: load_case(cid) for cid in CASES}
for name, fn in STRATS:
    t0 = time.time()
    prac, hold = [], []
    for cid in CASES:
        case, ans = data[cid]
        fc = fn(case)
        loss = score_case(fc, ans)[0]
        (prac if cid.startswith('p') else hold).append(loss)
    mp = sum(prac)/len(prac); mh = sum(hold)/len(hold)
    print(f"{name:20s} practice mean={mp:.4f}  [{', '.join(f'{v:.3f}' for v in prac)}]  holdout mean={mh:.4f}  [{', '.join(f'{v:.3f}' for v in hold)}]  ({time.time()-t0:.1f}s)")
