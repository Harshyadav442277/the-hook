"""Package compact scenario inference artifacts and benchmark simulation."""

from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path
import sys
from time import perf_counter

import joblib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import ARTIFACTS_DIR, PROCESSED_DATA_DIR, SCENARIO_DATA_DIR, SIMULATION_COUNT  # noqa: E402
from src.models.runtime import build_runtime_scenarios  # noqa: E402


def main() -> int:
    scenarios = json.loads(
        (SCENARIO_DATA_DIR / "scenarios.json").read_text(encoding="utf-8")
    )
    started = perf_counter()
    runtime = build_runtime_scenarios(
        scenarios,
        pd.read_parquet(PROCESSED_DATA_DIR / "pitcher_profiles.parquet"),
        pd.read_parquet(PROCESSED_DATA_DIR / "batter_profiles.parquet"),
        pd.read_parquet(PROCESSED_DATA_DIR / "pitcher_workload.parquet"),
        joblib.load(ARTIFACTS_DIR / "matchup_model.joblib"),
        joblib.load(ARTIFACTS_DIR / "win_expectancy_model.joblib"),
        simulation_count=SIMULATION_COUNT,
    )
    elapsed = perf_counter() - started
    output_path = ARTIFACTS_DIR / "runtime_scenarios.json"
    output_path.write_text(json.dumps(runtime, indent=2), encoding="utf-8")
    report = {
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "scenario_count": len(runtime),
        "simulation_count_per_candidate": SIMULATION_COUNT,
        "candidate_count": sum(len(item["default_ranking"]) for item in runtime),
        "elapsed_seconds": elapsed,
        "artifact_bytes": output_path.stat().st_size,
        "all_profiles_strictly_prior": all(
            evidence["profile_as_of_date"] is None
            or date.fromisoformat(evidence["profile_as_of_date"])
            < date.fromisoformat(scenario["game_date"])
            for scenario in runtime
            for evidence in scenario["candidate_evidence"]
        ),
    }
    (ARTIFACTS_DIR / "runtime_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
