"""Train and persist the transparent Phase 3 models."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import joblib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (  # noqa: E402
    ARTIFACTS_DIR,
    LEAGUE_PRIORS,
    OUTCOME_MAPPING_VERSION,
    PROCESSED_DATA_DIR,
    PROFILE_PRIOR_WEIGHT,
)
from src.models.matchup import (  # noqa: E402
    MATCHUP_FEATURES,
    train_matchup_model,
)
from src.models.win_expectancy import (  # noqa: E402
    STATE_FEATURES,
    train_win_expectancy_model,
)


def main() -> int:
    plate_appearances = pd.read_parquet(PROCESSED_DATA_DIR / "plate_appearances.parquet")
    states = pd.read_parquet(PROCESSED_DATA_DIR / "state_examples.parquet")
    matchup = train_matchup_model(plate_appearances)
    win_expectancy = train_win_expectancy_model(states)

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(matchup.pipeline, ARTIFACTS_DIR / "matchup_model.joblib")
    joblib.dump(win_expectancy.pipeline, ARTIFACTS_DIR / "win_expectancy_model.joblib")
    matchup.calibration.to_parquet(ARTIFACTS_DIR / "calibration.parquet", index=False)

    metadata = {
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "outcome_mapping_version": OUTCOME_MAPPING_VERSION,
        "profile_prior_weight": PROFILE_PRIOR_WEIGHT,
        "league_priors": LEAGUE_PRIORS,
        "matchup_features": MATCHUP_FEATURES,
        "state_features": STATE_FEATURES,
        "matchup_classes": matchup.metrics["classes"],
    }
    metrics = {
        "matchup": matchup.metrics,
        "win_expectancy": win_expectancy.metrics,
        "state_sanity": win_expectancy.sanity,
    }
    feature_schema = {
        "matchup_features": MATCHUP_FEATURES,
        "state_features": STATE_FEATURES,
        "matchup_classes": matchup.metrics["classes"],
    }
    for name, payload in (
        ("model_metadata.json", metadata),
        ("metrics.json", metrics),
        ("feature_schema.json", feature_schema),
    ):
        (ARTIFACTS_DIR / name).write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
