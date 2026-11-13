"""Loss decomposition + momentum/mean-reversion check."""
import sys, math
sys.path.insert(0, 'backtest')
from common import load_case, house_baseline, TAUS, pinball

# 1) baseline loss by tau level, and by jump vs quiet minutes (practice cases)
for cid in ['p00','p01','p02','p03','p04','p05']:
    case, ans = load_case(cid)
    base = house_baseline(case)
    by_tau = {t: [0.0, 0] for t in TAUS}
    jump_loss, jump_n, quiet_loss, quiet_n = 0.0, 0, 0.0, 0
    for mk in case['markets']:
        x = mk['prices'][-1]; ys = ans[mk['id']]; rows = base[mk['id']]
        for h in range(240):
            y = ys[h]
            is_jump = abs(y - x) > 0.02
            for t, q in zip(TAUS, rows[h]):
                v = pinball(y, q, t)
                by_tau[t][0] += v; by_tau[t][1] += 1
                if is_jump: jump_loss += v; jump_n += 1
                else: quiet_loss += v; quiet_n += 1
    tot = sum(v[0] for v in by_tau.values()); n = sum(v[1] for v in by_tau.values())
    print(f"{cid}: total={100*tot/n:.4f} | by tau: " +
          " ".join(f"{t}:{100*v[0]/v[1]:.3f}" for t, v in by_tau.items()) +
          f" | jump-min share={jump_n/n:.1%} loss={100*jump_loss/max(jump_n,1):.3f} | quiet loss={100*quiet_loss/max(quiet_n,1):.3f}")

# 2) momentum vs mean reversion: corr(d60_before, d240_after) across all practice+holdout market-cases
xs, ys = [], []
for cid in ['p00','p01','p02','p03','p04','p05','h03','h04']:
    case, ans = load_case(cid)
    for mk in case['markets']:
        p = mk['prices']
        if len(p) < 61: continue
        d60 = p[-1] - p[-61]
        d240 = ans[mk['id']][-1] - p[-1]
        xs.append(d60); ys.append(d240)
n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
cov = sum((a-mx)*(b-my) for a, b in zip(xs, ys))/n
sx = math.sqrt(sum((a-mx)**2 for a in xs)/n); sy = math.sqrt(sum((b-my)**2 for b in ys)/n)
print(f"\ncorr(d60_before, d240_after) = {cov/(sx*sy):.3f}  (n={n})")
# mean reversion ratio: E[d240 | |d60|>0.03] / d60
big = [(a, b) for a, b in zip(xs, ys) if abs(a) > 0.03]
if big:
    print(f"big-move cases (|d60|>0.03): n={len(big)}, mean d60={sum(a for a,_ in big)/len(big):+.3f}, mean d240={sum(b for _,b in big)/len(big):+.3f}, mean ratio d240/d60={sum(b/a for a,b in big)/len(big):+.2f}")
# 3) what happened in h00-h02? biggest single-market 240-min moves
for cid in ['h00','h01','h02']:
    case, ans = load_case(cid)
    moves = sorted(((abs(ans[mk['id']][-1]-mk['prices'][-1]), mk['name'], mk['prices'][-1], ans[mk['id']][-1]) for mk in case['markets']), reverse=True)
    print(f"{cid}: biggest 240m moves: " + "; ".join(f"{nm} {a:.3f}->{b:.3f}" for _, nm, a, b in moves[:3]))
