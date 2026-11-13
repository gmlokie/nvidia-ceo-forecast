# Final backtest results — main.py (validated 14 Nov ~02:00 WIB)

Pinball loss, percentage points. Baseline = exact house formula (q = x + z*0.0025*sqrt(h)).

| case | main.py | baseline |
|---|---|---|
| p00 | 0.5604 | 0.5323 |
| p01 | 0.3791 | 0.3795 |
| p02 | 0.4777 | 0.4189 |
| p03 | 0.3308 | 0.3618 |
| p04 | 0.2503 | 0.2946 |
| p05 | 0.1565 | 0.2387 |
| h00 | 2.3234 | 2.8140 |
| h01 | 1.3642 | 1.2752 |
| h02 | 3.1671 | 2.7912 |
| h03 | 0.1161 | 0.2226 |
| h04 | 0.1356 | 0.2424 |
| **practice mean** | **0.3592** | **0.3710** (official 0.363589) |
| **recent (p04, p05, h03, h04)** | **0.1647** | **0.2496** |
| **holdout mean** | **1.4213** | **1.4691** |

Runtime ~0.16 s/case (limit 8 s). Determinism verified byte-identical over 2 full runs.
Format validated on all 11 outputs (exactly one key `forecasts`, 240x5 per market,
non-decreasing, in [0,1], max 239 KB per file).
