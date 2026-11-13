"""Validate main.py outputs: format + score vs house baseline."""
import sys, json, os
sys.path.insert(0, 'backtest')
from common import load_case, score_case, house_baseline

tot_m, tot_b = [], []
for cid in ['p00','p01','p02','p03','p04','p05','h00','h01','h02','h03','h04']:
    case, ans = load_case(cid)
    out = json.load(open(f'/tmp/mf-out/{cid}.out'))
    assert set(out.keys()) == {'forecasts'}, out.keys()
    assert len(out['forecasts']) == len(case['markets'])
    fc = {}
    for row in out['forecasts']:
        assert set(row.keys()) == {'id', 'q'}
        assert len(row['q']) == 240 and all(len(r) == 5 for r in row['q'])
        assert all(0.0 <= v <= 1.0 for r in row['q'] for v in r)
        assert all(r[i] <= r[i+1] for r in row['q'] for i in range(4))
        fc[row['id']] = row['q']
    lm, med, cov, n = score_case(fc, ans)
    lb = score_case(house_baseline(case), ans)[0]
    tot_m.append(lm); tot_b.append(lb)
    print(f"{cid}: main.py={lm:.4f} baseline={lb:.4f}  (median_err={med:.3f} cov90={cov:.3f} bytes={os.path.getsize(f'/tmp/mf-out/{cid}.out')})")
print(f"\nPRACTICE mean: main.py={sum(tot_m[:6])/6:.4f} baseline={sum(tot_b[:6])/6:.4f} (official baseline 0.363589)")
print(f"RECENT (p04,p05,h03,h04): main.py={(tot_m[4]+tot_m[5]+tot_m[9]+tot_m[10])/4:.4f} baseline={(tot_b[4]+tot_b[5]+tot_b[9]+tot_b[10])/4:.4f}")
print(f"HOLDOUT mean: main.py={sum(tot_m[6:])/5:.4f} baseline={sum(tot_b[6:])/5:.4f}")
