"""Reversion profile + median-vs-band loss split + pooled-tail test."""
import sys, math
sys.path.insert(0, 'backtest')
from common import load_case, score_case, house_baseline, TAUS, pinball
import strategies as S
import strategies2 as D

CASES = ['p00','p01','p02','p03','p04','p05','h03','h04']
data = {cid: load_case(cid) for cid in CASES}

# 1) Reversion profile: mean (y(h)-x)/d60 for |d60|>0.03, by horizon bucket
buckets = [(1,15),(16,30),(31,60),(61,120),(121,180),(181,240)]
prof = {b: [] for b in buckets}
for cid in CASES:
    case, ans = data[cid]
    for mk in case['markets']:
        p = mk['prices']
        if len(p) < 61: continue
        d60 = p[-1] - p[-61]
        if abs(d60) <= 0.03: continue
        ys = ans[mk['id']]
        for (a,b) in buckets:
            prof[(a,b)].append(sum(ys[h-1]-p[-1] for h in range(a,b+1))/(b-a+1)/d60)
print("Reversion profile E[(y(h)-x)/d60] for |d60|>0.03:")
for b in buckets:
    v = prof[b]
    print(f"  h {b[0]:3d}-{b[1]:3d}: n={len(v):3d} mean={sum(v)/len(v):+.3f}")
# also for |d60| in (0.01,0.03]
prof2 = {b: [] for b in buckets}
for cid in CASES:
    case, ans = data[cid]
    for mk in case['markets']:
        p = mk['prices']
        if len(p) < 61: continue
        d60 = p[-1] - p[-61]
        if not (0.01 < abs(d60) <= 0.03): continue
        ys = ans[mk['id']]
        for (a,b) in buckets:
            prof2[(a,b)].append(sum(ys[h-1]-p[-1] for h in range(a,b+1))/(b-a+1)/d60)
print("Reversion profile for 0.01<|d60|<=0.03:")
for b in buckets:
    v = prof2[b]
    print(f"  h {b[0]:3d}-{b[1]:3d}: n={len(v):3d} mean={sum(v)/len(v):+.3f}" if v else f"  h {b}: n=0")

# 2) median-vs-band split on p05 and p00 for D floor0 rev0
for cid in ['p05','p00']:
    case, ans = data[cid]
    fc = D.forecast_D(case, win=1440, floor_out=0.0, rev_k=0.0)
    # oracle-median: replace median with actual y, keep D bands (shifted)
    orc = {}
    for mid, rows in fc.items():
        orc[mid] = []
        for h in range(240):
            y = ans[mid][h]; row = rows[h]
            new = [y + (q - row[2]) for q in row]
            new = sorted(min(1.0, max(0.0, v)) for v in new)
            orc[mid].append(new)
    print(f"{cid}: D={score_case(fc,ans)[0]:.4f}  oracle-median={score_case(orc,ans)[0]:.4f}  (band-only loss)")
    # oracle-bands: median = D median, bands = actual y (zero width) -> median-only loss
    orc2 = {}
    for mid, rows in fc.items():
        orc2[mid] = [[ans[mid][h]]*5 for h in range(240)]
    print(f"{cid}: oracle-bands(zero width, D median wrong)={score_case(orc2,ans)[0]:.4f}  (median-only loss)")
