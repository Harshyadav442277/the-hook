"""Build Phase 2 processed data, profiles, state examples, and scenarios."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (  # noqa: E402
    PHASE2_CHUNK_DAYS,
    PHASE2_END_DATE,
    PHASE2_START_DATE,
    PROCESSED_DATA_DIR,
    REPORTS_DIR,
    SCENARIO_DATA_DIR,
)
from src.data.acquire import load_cached_statcast_range  # noqa: E402
from src.data.prepare import (  # noqa: E402
    PROCESSING_COLUMNS,
    build_pitcher_workload,
    build_plate_appearances,
    build_state_examples,
)
from src.data.scenarios import (  # noqa: E402
    attach_player_names,
    find_scenario_candidates,
    resolve_mlb_player_names,
)
from src.features.profiles import (  # noqa: E402
    add_all_prior_features,
    build_monthly_profiles,
)


def main() -> int:
    pitches = load_cached_statcast_range(
        PHASE2_START_DATE,
        PHASE2_END_DATE,
        chunk_days=PHASE2_CHUNK_DAYS,
        columns=PROCESSING_COLUMNS,
    )
    plate_appearances, audit = build_plate_appearances(pitches)
    workload = build_pitcher_workload(pitches)
    featured = add_all_prior_features(plate_appearances)
    pitcher_profiles = build_monthly_profiles(featured, role="pitcher")
    batter_profiles = build_monthly_profiles(featured, role="batter")
    states = build_state_examples(featured)

    scenario_candidates = find_scenario_candidates(featured, workload, limit=12)
    if len(scenario_candidates) < 3:
        raise RuntimeError("Fewer than three valid scenario candidates were found")

    known_pitcher_names = {
        int(row.pitcher_id): str(row.pitcher_name)
        for row in workload[["pitcher_id", "pitcher_name"]]
        .dropna()
        .drop_duplicates("pitcher_id", keep="last")
        .itertuples(index=False)
    }
    all_player_ids = {
        int(value)
        for scenario in scenario_candidates
        for value in (
            [scenario["current_pitcher_id"], scenario["actual_choice_id"]]
            + list(scenario["candidate_reliever_ids"])
            + list(scenario["upcoming_batter_ids"])
        )
    }
    names = resolve_mlb_player_names(all_player_ids, known_names=known_pitcher_names)
    scenario_candidates = attach_player_names(scenario_candidates, names)

    # Top three are staged for manual review; no model output is used in their
    # selection. The first becomes the provisional flagship.
    selected = scenario_candidates[:3]
    selected[0]["is_flagship"] = True

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    SCENARIO_DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    featured.to_parquet(PROCESSED_DATA_DIR / "plate_appearances.parquet", index=False)
    pitcher_profiles.to_parquet(
        PROCESSED_DATA_DIR / "pitcher_profiles.parquet", index=False
    )
    batter_profiles.to_parquet(
        PROCESSED_DATA_DIR / "batter_profiles.parquet", index=False
    )
    workload.to_parquet(PROCESSED_DATA_DIR / "pitcher_workload.parquet", index=False)
    states.to_parquet(PROCESSED_DATA_DIR / "state_examples.parquet", index=False)
    (SCENARIO_DATA_DIR / "scenario_candidates.json").write_text(
        json.dumps(scenario_candidates, indent=2), encoding="utf-8"
    )
    (SCENARIO_DATA_DIR / "scenarios.json").write_text(
        json.dumps(selected, indent=2), encoding="utf-8"
    )

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_range": {"start": PHASE2_START_DATE, "end": PHASE2_END_DATE},
        **audit,
        "pitcher_profile_rows": int(len(pitcher_profiles)),
        "batter_profile_rows": int(len(batter_profiles)),
        "workload_rows": int(len(workload)),
        "state_example_rows": int(len(states)),
        "scenario_candidate_count": len(scenario_candidates),
        "selected_scenario_count": len(selected),
        "selected_scenario_ids": [value["scenario_id"] for value in selected],
        "manual_review_complete": all(value["manual_reviewed"] for value in selected),
        "artifact_sizes_bytes": {
            path.name: path.stat().st_size
            for path in PROCESSED_DATA_DIR.glob("*.parquet")
        },
    }
    (REPORTS_DIR / "phase2_build.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
