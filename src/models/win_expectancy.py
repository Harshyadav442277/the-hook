"""Simple chronological game-state win-expectancy model."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


STATE_FEATURES = [
    "inning",
    "outs_before",
    "on_1b_before",
    "on_2b_before",
    "on_3b_before",
    "fielding_team_is_home",
    "fielding_score_diff",
    "score_diff_x_inning",
]


@dataclass(frozen=True)
class WinExpectancyTrainingResult:
    pipeline: Pipeline
    metrics: dict[str, object]
    sanity: dict[str, object]


def prepare_state_features(states: pd.DataFrame) -> pd.DataFrame:
    result = states.copy()
    result["score_diff_x_inning"] = (
        pd.to_numeric(result["fielding_score_diff"], errors="coerce")
        * pd.to_numeric(result["inning"], errors="coerce")
    )
    for column in ("on_1b_before", "on_2b_before", "on_3b_before", "fielding_team_is_home"):
        result[column] = result[column].astype(int)
    return result


def _make_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("model", LogisticRegression(C=1.0, max_iter=300, solver="lbfgs")),
        ]
    )


def state_model_sanity(pipeline: Pipeline) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for inning in (5, 9):
        for score_diff in (-2, -1, 0, 1, 2):
            rows.append(
                {
                    "inning": inning,
                    "outs_before": 1,
                    "on_1b_before": False,
                    "on_2b_before": False,
                    "on_3b_before": False,
                    "fielding_team_is_home": True,
                    "fielding_score_diff": score_diff,
                }
            )
    grid = prepare_state_features(pd.DataFrame(rows))
    grid["probability"] = pipeline.predict_proba(grid[STATE_FEATURES])[:, 1]
    inning5 = grid.loc[grid["inning"].eq(5), "probability"].to_numpy()
    inning9 = grid.loc[grid["inning"].eq(9), "probability"].to_numpy()
    monotonic = bool(np.all(np.diff(inning5) > 0) and np.all(np.diff(inning9) > 0))
    magnifies = bool((inning9[-1] - inning9[0]) > (inning5[-1] - inning5[0]))
    return {
        "monotonic_in_score_diff": monotonic,
        "late_inning_magnifies_score": magnifies,
        "grid": [
            {
                "inning": int(row.inning),
                "score_diff": int(row.fielding_score_diff),
                "probability": float(row.probability),
            }
            for row in grid.itertuples(index=False)
        ],
        "pass": monotonic and magnifies,
    }


def train_win_expectancy_model(
    states: pd.DataFrame,
    *,
    train_end_date: str = "2025-12-31",
) -> WinExpectancyTrainingResult:
    frame = prepare_state_features(states)
    frame["game_date"] = pd.to_datetime(frame["game_date"])
    cutoff = pd.Timestamp(train_end_date)
    train = frame.loc[frame["game_date"].le(cutoff)].copy()
    holdout = frame.loc[frame["game_date"].gt(cutoff)].copy()
    if train.empty or holdout.empty:
        raise ValueError("Chronological state train and holdout sets must both be non-empty")

    pipeline = _make_pipeline()
    pipeline.fit(train[STATE_FEATURES], train["fielding_team_won"].astype(int))
    probability = pipeline.predict_proba(holdout[STATE_FEATURES])[:, 1]
    observed = holdout["fielding_team_won"].astype(int).to_numpy()
    baseline = np.full(len(holdout), train["fielding_team_won"].mean())
    sanity = state_model_sanity(pipeline)
    if not sanity["pass"]:
        raise RuntimeError(f"Win-expectancy sanity checks failed: {sanity}")

    metrics = {
        "model_type": "regularized_logistic_regression",
        "train_end_date": train_end_date,
        "train_rows": int(len(train)),
        "holdout_rows": int(len(holdout)),
        "log_loss": float(log_loss(observed, probability)),
        "baseline_log_loss": float(log_loss(observed, baseline)),
        "brier_score": float(brier_score_loss(observed, probability)),
        "baseline_brier_score": float(brier_score_loss(observed, baseline)),
        "features": STATE_FEATURES,
    }
    return WinExpectancyTrainingResult(
        pipeline=pipeline,
        metrics=metrics,
        sanity=sanity,
    )
