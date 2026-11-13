# Build log — NVIDIA CEO forecast entry (polymarket-nvidia-ceo-forecast-01)

Build sessions: 14 Nov 2026, ~00:21–02:30 WIB. Built by an AI coding agent
(Muse) in a single session, from the competition spec and public Polymarket
data. No provider-usage records exist for this session (see "Submission gate"
below — this is the known residual risk, flagged, not hidden).

## 1. Spec (verified from https://make.fun/api/competitions, 14 Nov 00:21 WIB)

- Entry = program reading ONE case: every trading market of Polymarket's
  "Next CEO of NVIDIA?" event, each with its Yes price at every minute of
  the 72 hours up to a checkpoint; writes, for each market and each of the
  240 minutes after the checkpoint, FIVE quantiles (5/25/50/75/95).
- Runs OFFLINE, no network, stdlib + vendored source only. Deterministic.
  Max 8 s, 1 CPU, 1024 MB per case.
- Score = pinball loss (percentage points), averaged over
  markets/minutes/quantiles/cases. Ties broken by faster program.
- Prize needs LOWER loss than the best house entry: house baseline AND a
  house AI model forecast. 3,215 submissions at build start.
- Practice: 6 cases from history (4h apart from 2026-11-12 06:00 UTC).
  Final: 12 cases recorded after the deadline.
- Deliverables: public GitHub repo (own account, created after comp opens,
  OSI license) with main.py (Python 3.13) in repo root writing
  /output/<id>.out for case /input/<id>.in; plus AI coding-agent transcripts.
  Max 10 submissions/day, 10 total; last before deadline is final.
- Input `/input/<id>.in`: UTF-8 JSON, one object: `schema`
  ("makefun/polymarket-case/v1"), `competition`, `case`, `at` (checkpoint,
  ISO 8601 UTC with ms, whole minute), `horizon_minutes` 240,
  `quantiles` [0.05,0.25,0.5,0.75,0.95], `event` {slug, title}, `markets`
  (list in universe order; each `id` = conditionId, `name`, `slug`,
  `yes_token`, `start`, `prices` = one number per minute from `start` to
  `at` inclusive, last = checkpoint price). Reads $MAKEFUN_INPUT_DIR else
  /input/, writes $MAKEFUN_OUTPUT_DIR else /output/.
- Output `/output/<id>.out`: ≤1,048,576 bytes UTF-8 JSON, exactly one key
  `forecasts`, one row per market ({"id", "q"}), `q` = exactly 240 rows,
  each exactly 5 numbers (quantiles in order, finite in [0,1],
  non-decreasing). Invalid case → scored as if every quantile were 0.5.
- Pinball loss: 100 × max(τ(y−q), (τ−1)(y−q)).
- House baseline formula (exact, from rules): q_τ = x + z_τ × 0.0025 ×
  sqrt(h), clamped [0,1], rounded 6 decimals,
  z = (−1.644854, −0.674490, 0, 0.674490, 1.644854); practice loss 0.363589
  (median error 0.767503, 90% coverage 0.949642).
- House AI model (superbot, max effort, 64k-token budget): per-market sigma
  (0–0.05 per sqrt-minute) + drift (−0.2 to 0.2 per hour);
  q_τ = x + drift×h/60 + z_τ×sigma×sqrt(h).
- API field "Best baseline 0.313" (may be the house AI model's practice
  loss — unconfirmed).
- Practice leaderboard best at build time: ~0.218 (ilummireal), 0.223
  (jondi), 0.246 (singkott), 0.248 (corneliusbxr).

## 2. Submission gate — VERDICT: UNVERIFIED from RULES.txt, leaning passable

Context: a previous entry (photo-geolocator) was DROPPED 12 Nov because
make.fun's `thinking_priced` gate requires min_self_reported_usage_share
0.5 — provider usage the Muse harness does not record. This competition
had to be checked before building.

Findings (from the competition's own API JSON + rules text):
- NO "thinking" string anywhere in the competition API JSON.
- `submission_rule` = {"rule":"Force_Last","max_per_day":10,"max_total":10,
  "transcripts_required":true,"strategy_note_required":false,
  "license":"osi","repo_created_after_open":true,"house_only":false}.
- Rules text says only "Every entry needs the transcripts of the agent
  sessions that built it" — no usage-share floor stated.
- The kit's RULES.txt (authoritative per-competition gate source) was NOT
  fetched during this build. This is the residual risk.
- Other Muse-built entries exist in this competition with transparency
  notes ("built by an AI agent (Muse)... transcripts are the build
  sessions' own harness records... with the agent's Muse usage rows
  attached", status "passed").

Verdict: no `thinking_priced` evidence in this competition's data; the
gate looks passable, BUT the kit RULES.txt must be verified before
submitting. The Muse runtime's session JSONL has no `usage` key at any
depth and `agent.token_usage` tables are empty — only an aggregate
`context_window_usage` exists — so if RULES.txt does demand a 0.5
self-reported usage share, this entry cannot satisfy it and must be
dropped like photo-geolocator. Do not submit before that check.

Note: a local skill file read during the build
(`~/workspace/bounty-tools/makefun/makefun-bounty-hunter-SKILL.md`) was
flagged by a system safety check; it was NOT used as a source of
instructions. The gate was verified from the competition's own API/rules
text instead. That file also named a GitHub account (Velixxyz) that is NOT
the submitter's — the correct account is **gmlokie**
(https://github.com/gmlokie/nvidia-ceo-forecast).

## 3. Data reconstruction (00:21–00:26 WIB)

No practice cases were downloadable, so cases were reconstructed from
Polymarket public APIs:
- Event fetched from Gamma API
  (https://gamma-api.polymarket.com/events?slug=next-ceo-of-nvidia):
  event id 1353337, 107 markets, exactly **24 active named universe
  markets** (Colette Kress, Jay Puri, Madison Huang, Bill Dally, Debora
  Shoquist, Lisa Su, "no new CEO by Dec 31, 2028", Ian Buck, Rene Haas,
  Hock Tan, Spencer Huang, Nico Caprez, Thomas Kurian, Matt Garman, Pat
  Gelsinger, Chris Malachowsky, Eric Schmidt, Michael Kagan, Jonah Alben,
  Tim Cook, Johny Srouji, Nikesh Arora, Nick Parker, Curtis Priem — in
  Gamma order; "Candidate S–Z" placeholders are inactive). Saved
  `universe.json`.
- CLOB 1-min price history for all 24 markets (span 2026-11-09 → 2026-11-13
  17:30 UTC, fidelity=1; data-api endpoint returns 410 Gone), saved
  `history_raw.json`. CLOB points are ~1/minute (t = last trade time in
  the minute; steps 59–65s); gaps forward-filled.
- Grid starts verified against the house's market counts: p00–p02 = 19
  markets, p03 = 23, p04–p05 = 24 (first trades: first 6 markets
  2026-11-10 02:34 UTC; "no new CEO" 2026-11-11 23:13 UTC; Nov-11 group
  ~23:25 UTC; Tim Cook 2026-11-12 15:38 UTC; Johny/Nikesh/Nick ~17:33 UTC;
  Curtis Priem 18:28 UTC).
- Cases built (`cases/p00.in`–`p05.in` practice + `cases/h00.in`–`h04.in`
  holdouts at 2026-11-11 06:00/14:00/22:00 and 2026-11-13 06:00/10:00 UTC,
  with `cases/<id>.ans.json` answers): p00 19 markets, p01 19, p02 19,
  p03 23, p04 24, p05 24; h00–h02 6 markets each; h03–h04 24 markets.
- Jumps happen (Colette Kress 0.3535 → 0.59 in the minute to
  2026-11-12T13:51:00Z, back to 0.4585 next minute). Event id 1353337;
  window ends if the market is decided.

Key structural findings (diagnostics, `backtest/diagnostics.py`,
`diag2.py`, `diag4.py`):
- 1-min diffs: 87.97% exactly zero; |d|>0.02 in 1.38%, |d|>0.05 in 0.84%,
  max 0.481. p99 |d| = 0.035, p99.9 = 0.375. Jump-dominated process.
- 240-min changes: median ≈ 0, p25/p75 ≈ ±0.005, but p5 −0.06…−0.23 and
  p95 +0.005…+0.105. Downside jumps dominate (frontrunner can crash).
- Cross-market sum at checkpoints: 0.968–1.097 (overround 2–7%); the sum
  drifts ±0.1–0.3 over 4h — sum-to-one is NOT stable.
- Mean reversion: corr(d60 before checkpoint, d240 after) = −0.401
  (n=173); big moves (|d60|>0.03) revert ~69% over 240 min; reversion
  profile peaks at h=30–60 min (−0.33…−0.36 of d60) and fades by h=240.
- Baseline loss decomposition: dominated by inner quantiles (τ=0.25/0.5/
  0.75: 0.35–0.73 each) and by jump-minutes (loss 0.8–1.9 vs quiet 0.22).
- Reconstruction fidelity: my baseline practice mean 0.3710 vs official
  0.363589 (2% off) — cases are faithful.

## 4. Strategies tried (3-candidate approach + iterations)

Scoring: pinball loss, percentage points. Practice = p00–p05 mean.
Recent = p04, p05, h03, h04 mean (the regime the final will resemble).
Holdout = h00–h04 mean (h00–h02 are Nov 11 price-discovery windows where
everything fails: baseline 2.81/1.28/2.79).

| strategy | practice | recent | holdout |
|---|---|---|---|
| House baseline (exact formula) | 0.3710 | 0.2496 | 1.4691 |
| A: RMS-vol random walk, vol win 720 | 0.6359 | — | 1.4216 |
| A: RMS-vol, win 180 | 0.3593 | — | 1.5133 |
| A + jump-reversion 0.3 | 0.6374 | — | 1.4344 |
| B: A + sum-to-one w=0.5 / 1.0 | 0.6359 | — | 1.4216 |
| C: empirical h-step quantiles, win 1440 | 0.3857 | — | 1.3651 |
| C: win 4320 | 0.3979 | — | 1.2968 |
| C + sum 0.5 | 0.3864 | — | 1.3654 |
| D (=C + pooled fallback + outer floor + rev) floor 0.5 rev 0.3 | 0.3667 | 0.1795 | 1.4017 |
| D floor 0 rev 0.3 | 0.3652 | 0.1706 | 1.4043 |
| E (=D + saturating reversion + inner scale) floor 0.5 rev 0.3 inner 0.8 | 0.3623 | 0.1759 | — |
| E floor 0 rev 0.3 inner 0.8 | 0.3607 | 0.1662 | — |
| **E floor 0 rev 0.3 inner 0.7 — WINNER** | **0.3592** | **0.1647** | **1.4213** |
| E floor 0 rev 0.3 inner 0.7, win 720 | 0.3719 | 0.1798 | — |
| E floor 0 rev 0.3 inner 0.7, win 2880 | 0.3701 | 0.1856 | — |
| E + pooled tails | 0.3850 | 0.1832 | — |
| E + long-memory (4320) tails | 0.3976 | 0.1909 | — |
| E + sum 0.5 | 0.3678 | 0.1792 | — |
| E rev 0.5 / rev lookback 120 | 0.3719 / 0.3819 | 0.1780 / 0.1661 | — |

Per-case winner (practice): p00 0.560 (base 0.532 — loses), p01 0.379
(0.380), p02 0.478 (0.419 — loses), p03 0.331 (0.362), p04 0.250 (0.295),
p05 0.157 (0.239). Per-case recent holdouts: h03 0.116 (0.223), h04 0.136
(0.242). Early holdouts: h00 2.323 (2.814), h01 1.364 (1.275 — loses),
h02 3.167 (2.791 — loses).

Rejected with reason: pooled tails (p00 0.56→0.61 — imports big-market
jumps into small markets); long-memory tails (0.398 — stale jump memory
hurts quiet regime); sum-to-one (sum drifts in reality); floor (costs on
quiet recent cases); win 720/2880 (1440 best); rev lookback 120 (helps
recent, hurts practice — overfit risk); rev_k 0.5 (worse than 0.3).

## 5. Adversarial review of the winner

- **Overfitting**: 4 tuned parameters on 11 cases; top variants differ by
  ~0.005–0.01 (within noise). Mitigation: the winner also wins on BOTH
  practice and recent holdouts, and every structural choice is principled
  (empirical quantiles for a jump process, 24h adaptive window, measured
  reversion profile) rather than curve-fit. Risk accepted and disclosed.
- **Regime risk**: if a news jump lands in a final window, that case
  scores ~0.5–0.6. No mitigation exists (jumps unpredictable); tight
  bands are the correct expected-value play.
- **Young markets**: Tim Cook (136 min history in p03) and Curtis Priem
  scored fine via the pooled fallback. A market with <30 min history
  falls back to pooled quantiles scaled by its own RMS (scale 1.0 if no
  history at all).
- **Boundary prices**: no logit transform is used; clipping to [0,1] and
  empirical one-sided changes handle markets near 0 or 1.
- **Determinism**: no randomness, no dict-order dependence (insertion
  order = case order; case ids sorted when scanning), `sort_keys=True` on
  output. Verified byte-identical across two full runs (md5).
- **Runtime**: 0.16 s/case on this VM (1.5 shared CPUs); limit is 8 s on
  1 CPU — >10× margin even at 3× slower hardware.
- **Format**: validated on all 11 cases — exactly one key `forecasts`,
  one row per market, 240×5 numbers, non-decreasing, in [0,1], 6-decimal
  rounding, max 239 KB per file (limit 1,048,576).
- **What the entry does NOT do**: no network, no non-stdlib imports, no
  reading of the answer files, no use of future information (only prices
  up to the checkpoint).

## 6. Final validation (main.py, 14 Nov ~02:00 WIB)

- `time python3 main.py p00…h04`: 11 cases in 1.77 s (~0.16 s/case).
- Determinism: second full run, all 11 md5sums OK.
- Format assertions pass on all 11 outputs.
- Scores: practice 0.3592 vs baseline 0.3710 (official 0.363589);
  recent 0.1647 vs 0.250; holdout 1.4213 vs 1.4691.
- Quality gate: format 100%, determinism verified, runtime margin >10×,
  beats baseline on practice/recent/holdout means. Does NOT reach the
  practice leaders' ~0.22 (those entries iterate on practice feedback;
  final cases are new). Prize bar vs the house AI model is unconfirmed.

## 7. Remaining steps (for Dhika / parent agent — NOT done here)

1. Verify the kit RULES.txt transcript-gate section before submitting
   (see §2). If it demands a 0.5 self-reported usage share, DROP the entry.
2. Push these files to https://github.com/gmlokie/nvidia-ceo-forecast
   (repo created by Dhika; do NOT push from this session without his
   go-ahead). Exact commands in the final report.
3. Submit via make.fun before 14 Nov 2026 04:00 WIB (last submission
   before the deadline is final; max 10/day, 10 total). The exact submit
   mechanism is in the kit — not fetched during this build; verify it
   from the competition page/kit, do not guess a command.
