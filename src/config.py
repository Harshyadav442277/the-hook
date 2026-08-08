"""Shared project configuration.

Only constants required by the active data-foundation work live here. Later
phases may add model and simulation settings when those components exist.
"""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
REPORTS_DIR = PROJECT_ROOT / "reports"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SCENARIO_DATA_DIR = DATA_DIR / "scenarios"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

# Small, completed regular-season window used only to prove acquisition and
# schema compatibility. Phase 2 performs the larger bounded acquisition.
PROBE_START_DATE = "2026-07-01"
PROBE_END_DATE = "2026-07-02"
PROBE_CHUNK_DAYS = 1

# Frozen Phase 2 window. It covers one complete recent season plus 2026 YTD
# without adding 2024 preemptively.
PHASE2_START_DATE = "2025-03-27"
PHASE2_END_DATE = "2026-08-07"
PHASE2_CHUNK_DAYS = 7

OUTCOME_MAPPING_VERSION = "1.0"

# Fixed, pre-model pooling priors. These are intentionally conservative and
# avoid learning a league prior from future rows. Phase 3 validates whether the
# resulting features beat a league-rate baseline.
PROFILE_PRIOR_WEIGHT = 200.0
LEAGUE_PRIORS = {
    "OUT": 0.700,
    "FREE_PASS": 0.090,
    "SINGLE": 0.150,
    "EXTRA_BASE": 0.060,
    "K_RATE": 0.230,
    "WALK_RATE": 0.085,
    "WOBA": 0.315,
}

SIMULATION_COUNT = 2_000
EFFECTIVE_TIE_THRESHOLD = 0.005
