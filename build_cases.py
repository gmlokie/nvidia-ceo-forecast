"""Build minute grids + practice/holdout cases in the exact make.fun format.
Grid: per market, one price per minute from first trade minute, forward-filled.
Cases: practice p00-p05 (checkpoints 2026-11-12 06:00 UTC +4h), holdouts
h00-h04 (2026-11-11 06:00, 14:00, 22:00; 2026-11-13 06:00, 10:00 UTC).
Writes cases/<id>.in (exact format) and cases/<id>.ans.json (answers for scoring).
"""
import json, datetime, os

def dt(y,mo,d,h,mi=0):
    return datetime.datetime(y,mo,d,h,mi,tzinfo=datetime.timezone.utc)
def ts(d): return int(d.timestamp())
def iso(t): return datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
def short_name(q):
    if q.startswith('Will ') and q.endswith(' be the next CEO of NVIDIA?'):
        return q[5:-len(' be the next CEO of NVIDIA?')]
    if 'no new' in q.lower():
        return 'No new CEO by Dec 31, 2028'
    return q

raw = json.load(open('history_raw.json'))
uni = json.load(open('universe.json'))
span_start, span_end = raw['start'], raw['end']

# --- minute grids: bucket = (t//60)*60, last point in bucket wins, forward-fill ---
grids = {}
for m in uni:
    pts = raw['hist'][m['conditionId']]
    buck = {}
    for p in pts:
        b = (p['t'] // 60) * 60
        buck[b] = p['p']
    if not buck:
        continue
    first, last = min(buck), max(buck)
    grid = {}
    cur = None
    for minute in range(first, last + 60, 60):
        if minute in buck:
            cur = buck[minute]
        if cur is not None:
            grid[minute] = cur
    grids[m['conditionId']] = {'start': first, 'grid': grid}
    print(f"{m['question'][:40]:40s} grid {iso(first)} -> {iso(last)}  minutes={len(grid)}")

os.makedirs('cases', exist_ok=True)
checkpoints = {
    'p00': dt(2026,11,12,6), 'p01': dt(2026,11,12,10), 'p02': dt(2026,11,12,14),
    'p03': dt(2026,11,12,18), 'p04': dt(2026,11,12,22), 'p05': dt(2026,11,13,2),
    'h00': dt(2026,11,11,6), 'h01': dt(2026,11,11,14), 'h02': dt(2026,11,11,22),
    'h03': dt(2026,11,13,6), 'h04': dt(2026,11,13,10),
}
for cid, cp in checkpoints.items():
    at = ts(cp)
    markets, answers = [], {}
    for m in uni:
        g = grids.get(m['conditionId'])
        if g is None or g['start'] > at:
            continue
        lo = max(at - 72*3600, g['start'])
        prices = [g['grid'][minute] for minute in range(lo, at + 60, 60)]
        markets.append({
            'id': m['conditionId'], 'name': short_name(m['question']),
            'slug': m['slug'], 'yes_token': m['yes_token'],
            'start': iso(lo), 'prices': prices})
        # answers: minutes at+60 .. at+240*60 (must exist in grid)
        ans = []
        ok = True
        for k in range(1, 241):
            minute = at + k*60
            if minute in g['grid']:
                ans.append(g['grid'][minute])
            else:
                ok = False; break
        if not ok:
            print(f"  WARN {cid} {m['question'][:30]}: answers incomplete at minute {k}")
            ans = ans + [ans[-1]] * (240 - len(ans)) if ans else [0.5]*240
        answers[m['conditionId']] = ans
    case = {
        'schema': 'makefun/polymarket-case/v1',
        'competition': 'polymarket-nvidia-ceo-forecast-01',
        'case': cid, 'at': iso(at), 'horizon_minutes': 240,
        'quantiles': [0.05, 0.25, 0.5, 0.75, 0.95],
        'event': {'slug': 'next-ceo-of-nvidia', 'title': 'Next CEO of NVIDIA?'},
        'markets': markets,
    }
    with open(f'cases/{cid}.in', 'w') as f:
        f.write(json.dumps(case, sort_keys=True, separators=(',', ':')))
    json.dump(answers, open(f'cases/{cid}.ans.json', 'w'))
    n72 = sum(1 for mk in markets if len(mk['prices']) >= 4320)
    print(f"{cid} at={iso(at)} markets={len(markets)} (full-72h: {n72}) "
          f"price-len range={min(len(mk['prices']) for mk in markets)}..{max(len(mk['prices']) for mk in markets)}")
print("done")
