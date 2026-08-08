"""Fail-closed validation for the public/deployed artifact bundle."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import joblib
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import ARTIFACTS_DIR, REPORTS_DIR  # noqa: E402


REQUIRED = {
    "runtime_scenarios.json",
    "metrics.json",
    "model_metadata.json",
    "feature_schema.json",
    "calibration.parquet",
    "matchup_model.joblib",
    "win_expectancy_model.joblib",
}


def main() -> int:
    missing = sorted(name for name in REQUIRED if not (ARTIFACTS_DIR / name).exists())
    if missing:
        raise FileNotFoundError(f"Missing public artifacts: {missing}")
    scenarios = json.loads(
        (ARTIFACTS_DIR / "runtime_scenarios.json").read_text(encoding="utf-8")
    )
    joblib.load(ARTIFACTS_DIR / "matchup_model.joblib")
    joblib.load(ARTIFACTS_DIR / "win_expectancy_model.joblib")

    failures: list[str] = []
    if len(scenarios) != 3:
        failures.append("expected exactly three scenarios")
    if sum(bool(item.get("is_flagship")) for item in scenarios) != 1:
        failures.append("expected exactly one flagship")
    for scenario in scenarios:
        candidates = scenario["candidate_reliever_ids"]
        if not 3 <= len(candidates) <= 5:
            failures.append(f"{scenario['scenario_id']}: invalid candidate count")
        if scenario["actual_choice_id"] not in candidates:
            failures.append(f"{scenario['scenario_id']}: actual choice missing")
        if not scenario.get("manual_reviewed"):
            failures.append(f"{scenario['scenario_id']}: source review missing")
        for candidate_id in candidates:
            matrix = np.asarray(scenario["matchup_probabilities"][str(candidate_id)])
            if matrix.shape != (3, 4) or not np.allclose(matrix.sum(axis=1), 1.0):
                failures.append(f"{scenario['scenario_id']}/{candidate_id}: invalid matrix")
    runtime_source = (PROJECT_ROOT / "app.py").read_text(encoding="utf-8") + (
        PROJECT_ROOT / "pages" / "1_How_It_Works.py"
    ).read_text(encoding="utf-8")
    if "requests" in runtime_source or "pybaseball" in runtime_source:
        failures.append("runtime page imports a network acquisition client")
    artifact_bytes = sum(path.stat().st_size for path in ARTIFACTS_DIR.iterdir())
    if artifact_bytes > 50 * 1024 * 1024:
        failures.append("public artifact bundle exceeds 50 MB target")

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "passed": not failures,
        "failures": failures,
        "scenario_count": len(scenarios),
        "flagship_count": sum(bool(item.get("is_flagship")) for item in scenarios),
        "candidate_count": sum(len(item["candidate_reliever_ids"]) for item in scenarios),
        "artifact_bytes": artifact_bytes,
        "runtime_network_clients": False,
        "models_load_in_fresh_process": True,
    }
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "final_validation.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
