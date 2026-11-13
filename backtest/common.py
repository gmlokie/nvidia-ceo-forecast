"""Shared backtest utilities: pinball scoring + house baseline (exact formulas)."""
import json, math

TAUS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.6448536269514722, -0.6744897501960817, 0.0, 0.6744897501960817, 1.6448536269514722]

def pinball(y, q, tau):
    d = y - q
    return max(tau * d, (tau - 1.0) * d)  # in price units

def score_case(forecast, answers):
    """forecast: {market_id: [[q5,q25,q50,q75,q95] x 240]}; answers: {id: [240 prices]}.
    Returns (mean pinball in percentage points, median abs err pp, 90% coverage, n_items)."""
    tot = 0.0; n = 0; med_err = 0.0; cov = 0
    for mid, rows in forecast.items():
        ys = answers[mid]
        for h in range(240):
            y = ys[h]
            qs = rows[h]
            med_err += abs(y - qs[2])
            if qs[0] <= y <= qs[4]:
                cov += 1
            for t, q in zip(TAUS, qs):
                tot += pinball(y, q, t); n += 1
    return 100.0 * tot / n, 100.0 * med_err / (n // 5), cov / (n // 5), n

def house_baseline(case):
    """Exact house baseline: q_tau = x + z_tau * 0.0025 * sqrt(h), clamp [0,1], round 6dp."""
    out = {}
    for mk in case['markets']:
        x = mk['prices'][-1]
        rows = []
        for h in range(1, 241):
            s = 0.0025 * math.sqrt(h)
            rows.append([round(min(1.0, max(0.0, x + z * s)), 6) for z in Z])
        out[mk['id']] = rows
    return out

def load_case(cid):
    case = json.load(open(f'cases/{cid}.in'))
    ans = json.load(open(f'cases/{cid}.ans.json'))
    return case, ans

def check_sum_to_one(case):
    """Sum of last prices across markets at checkpoint (structure check)."""
    return sum(mk['prices'][-1] for mk in case['markets'])
