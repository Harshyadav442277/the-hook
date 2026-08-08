# Phase 1 Statcast Data Probe

Status: **PASS**  
Generated: 2026-08-08T08:05:05.751985+00:00  
Requested range: 2025-03-27 through 2026-08-07  
Python: 3.12.2  

## Acquisition

- Rows: 1,274,390
- Columns: 119
- Chunks: 72
- Cache hits: 32
- Cache misses/downloads: 40
- Source: MLB Statcast/Baseball Savant via pybaseball

## Schema

- Schema gate: PASS
- Missing required columns: None
- Workload support: days of rest is available directly as `pitcher_days_since_prev_game`; recent pitch counts are derivable by pitcher/game/date from pitch rows.

## Terminal-event mapping

- Terminal events: 327,756
- Canonically mapped: 324,435 (98.99%)
- Documented exclusions: 3,321
- Accounted for: 100.00%
- Unknown events: None

### Canonical outcome counts

- `EXTRA_BASE`: 24,965
- `FREE_PASS`: 31,870
- `OUT`: 221,159
- `SINGLE`: 46,441

### Documented exclusions

- `catcher_interf`
- `field_error`
- `fielders_choice`
- `runner_double_play`
- `truncated_pa`

## Phase 2 decision

Use 2025-03-27 through 2026-08-07 in seven-day cached chunks. Do not add 2024 unless Phase 2 exposes an evidence-based cold-start or sample-coverage problem.
