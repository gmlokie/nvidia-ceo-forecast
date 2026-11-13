"""Quick structural diagnostics on the reconstructed cases."""
import sys, math, statistics
sys.path.insert(0, 'backtest')
from common import load_case

def pct(v, q):
    s = sorted(v); i = min(len(s)-1, max(0, int(q*len(s))))
    return s[i]

for cid in ['p00','p01','p02','p03','p04','p05','h03','h04']:
    case, ans = load_case(cid)
    d240, d60, sums0, sums240 = [], [], 0.0, 0.0
    for mk in case['markets']:
        p = mk['prices']; x = p[-1]
        sums0 += x; sums240 += ans[mk['id']][-1]
        d240.append(ans[mk['id']][-1] - x)
        d60.append(ans[mk['id']][59] - x)
    print(f"{cid}: sum0={sums0:.3f} sum240={sums240:.3f} | d240: p5={pct(d240,0.05):+.3f} p25={pct(d240,0.25):+.3f} med={pct(d240,0.5):+.3f} p75={pct(d240,0.75):+.3f} p95={pct(d240,0.95):+.3f} | zero240={sum(1 for d in d240 if d==0)}/{len(d240)} | mean|d240|={sum(abs(d) for d in d240)/len(d240):.4f} | mean|d60|={sum(abs(d) for d in d60)/len(d60):.4f}")

# jump frequency in history: 1-min |diff| distribution over all markets/cases
alld = []
for cid in ['p00','p03','p05']:
    case, _ = load_case(cid)
    for mk in case['markets']:
        p = mk['prices']
        alld += [p[i+1]-p[i] for i in range(len(p)-1)]
print(f"\n1-min diffs n={len(alld)}: zero={sum(1 for d in alld if d==0)/len(alld):.2%} | |d|>0.02: {sum(1 for d in alld if abs(d)>0.02)/len(alld):.3%} | |d|>0.05: {sum(1 for d in alld if abs(d)>0.05)/len(alld):.4%} | max|d|={max(abs(d) for d in alld):.3f}")
print(f"1-min |d| percentiles: p50={pct([abs(d) for d in alld],0.5):.4f} p90={pct([abs(d) for d in alld],0.9):.4f} p99={pct([abs(d) for d in alld],0.99):.4f} p999={pct([abs(d) for d in alld],0.999):.4f}")
