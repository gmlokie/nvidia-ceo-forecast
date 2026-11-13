"""Fetch 1-min CLOB price history for all 24 universe markets.
Span: 2026-11-09 00:00 UTC -> 2026-11-13 17:30 UTC (covers practice + holdouts).
Saves raw histories to history_raw.json (token -> list of {t,p}).
"""
import json, urllib.request, urllib.error, datetime, time, sys

uni = json.load(open('universe.json'))
start = int(datetime.datetime(2026,11,9,0,0,tzinfo=datetime.timezone.utc).timestamp())
end = int(datetime.datetime(2026,11,13,17,30,tzinfo=datetime.timezone.utc).timestamp())

def fetch(token, tries=3):
    url = f"https://clob.polymarket.com/prices-history?market={token}&startTs={start}&endTs={end}&fidelity=1"
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)['history']
        except Exception as e:
            print(f"  retry {i+1} {token[:12]}: {e}", file=sys.stderr)
            time.sleep(2)
    raise RuntimeError(f"failed {token}")

out = {}
for m in uni:
    h = fetch(m['yes_token'])
    out[m['conditionId']] = h
    print(f"{m['question'][:45]:45s} {len(h)} pts  first={h[0]['t']} last={h[-1]['t']}")
    time.sleep(0.3)

json.dump({'start': start, 'end': end, 'hist': out}, open('history_raw.json','w'))
print("saved history_raw.json, markets:", len(out))
