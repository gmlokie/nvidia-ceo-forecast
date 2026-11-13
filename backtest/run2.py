import sys, time
sys.path.insert(0, 'backtest')
from common import load_case, score_case, house_baseline
import strategies2 as D

CASES = ['p00','p01','p02','p03','p04','p05','h00','h01','h02','h03','h04']
data = {cid: load_case(cid) for cid in CASES}
def ev(fn):
    prac, hold = [], []
    for cid in CASES:
        case, ans = data[cid]
        loss = score_case(fn(case), ans)[0]
        (prac if cid.startswith('p') else hold).append(loss)
    return sum(prac)/6, sum(hold)/5, prac, hold

print("BASELINE:", [round(v,3) for v in ev(lambda c: house_baseline(c))[:2]])
for floor_out in [0.0, 0.5, 0.75, 1.0]:
    for rev_k in [0.0, 0.3, 0.5]:
        mp, mh, prac, hold = ev(lambda c, f=floor_out, k=rev_k: D.forecast_D(c, win=1440, floor_out=f, rev_k=k))
        print(f"D win1440 floor={floor_out} rev={rev_k}: prac={mp:.4f} [{', '.join(f'{v:.3f}' for v in prac)}] hold={mh:.4f} recent_hold(h03,h04)={sum(hold[3:])/2:.4f}")
