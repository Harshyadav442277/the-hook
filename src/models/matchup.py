"""Four-outcome regularized matchup model and compact validation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


MATCHUP_NUMERIC_FEATURES = [
    "pitcher_pa_before",
    "pitcher_out_rate",
    "pitcher_free_pass_rate",
    "pitcher_single_rate",
    "pitcher_extra_base_rate",
    "pitcher_k_rate",
    "pitcher_walk_rate",
    "pitcher_woba",
    "batter_pa_before",
    "batter_out_rate",
    "batter_free_pass_rate",
    "batter_single_rate",
    "batter_extra_base_rate",
    "batter_k_rate",
    "batter_walk_rate",
    "batter_woba",
    "pitcher_days_since_prev_game",
]
MATCHUP_CATEGORICAL_FEATURES = ["pitcher_hand", "batter_stand"]
MATCHUP_FEATURES = MATCHUP_NUMERIC_FEATURES + MATCHUP_CATEGORICAL_FEATURES


@dataclass(frozen=True)
class MatchupTrainingResult:
    pipeline: Pipeline
    metrics: dict[str, object]
    calibration: pd.DataFrame


def _make_pipeline() -> Pipeline:
    preprocessing = ColumnTransformer(
        [
            (
                "numeric",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler()),
                    ]
                ),
                MATCHUP_NUMERIC_FEATURES,
            ),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                MATCHUP_CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )
    return Pipeline(
        [
            ("preprocess", preprocessing),
            (
                "model",
                LogisticRegression(
                    C=1.0,
                    max_iter=500,
                    solver="lbfgs",
                    class_weight=None,
                ),
            ),
        ]
    )


def _calibration_frame(probability: np.ndarray, observed: np.ndarray) -> pd.DataFrame:
    frame = pd.DataFrame({"predicted": probability, "observed": observed.astype(float)})
    frame["bin"] = pd.cut(
        frame["predicted"], bins=np.linspace(0.0, 1.0, 11), include_lowest=True
    )
    return (
        frame.groupby("bin", observed=True)
        .agg(
            mean_predicted=("predicted", "mean"),
            observed_rate=("observed", "mean"),
            count=("observed", "size"),
        )
        .reset_index(drop=True)
    )


def train_matchup_model(
    plate_appearances: pd.DataFrame,
    *,
    train_end_date: str = "2025-12-31",
) -> MatchupTrainingResult:
    """Train on past PAs and validate strictly on later PAs."""

    frame = plate_appearances.copy()
    frame["game_date"] = pd.to_datetime(frame["game_date"])
    cutoff = pd.Timestamp(train_end_date)
    train = frame.loc[frame["game_date"].le(cutoff)].copy()
    holdout = frame.loc[frame["game_date"].gt(cutoff)].copy()
    if train.empty or holdout.empty:
        raise ValueError("Chronological train and holdout sets must both be non-empty")

    pipeline = _make_pipeline()
    pipeline.fit(train[MATCHUP_FEATURES], train["outcome_class"])
    probabilities = pipeline.predict_proba(holdout[MATCHUP_FEATURES])
    classes = list(pipeline.named_steps["model"].classes_)

    train_frequencies = (
        train["outcome_class"].value_counts(normalize=True).reindex(classes, fill_value=0.0)
    )
    baseline_probabilities = np.tile(train_frequencies.to_numpy(), (len(holdout), 1))
    model_log_loss = log_loss(holdout["outcome_class"], probabilities, labels=classes)
    baseline_log_loss = log_loss(
        holdout["outcome_class"], baseline_probabilities, labels=classes
    )

    out_index = classes.index("OUT")
    on_base_probability = 1.0 - probabilities[:, out_index]
    observed_on_base = holdout["outcome_class"].ne("OUT").to_numpy()
    calibration = _calibration_frame(on_base_probability, observed_on_base)

    metrics = {
        "model_type": "regularized_multinomial_logistic_regression",
        "train_end_date": train_end_date,
        "train_date_min": train["game_date"].min().date().isoformat(),
        "train_date_max": train["game_date"].max().date().isoformat(),
        "holdout_date_min": holdout["game_date"].min().date().isoformat(),
        "holdout_date_max": holdout["game_date"].max().date().isoformat(),
        "train_rows": int(len(train)),
        "holdout_rows": int(len(holdout)),
        "classes": classes,
        "multiclass_log_loss": float(model_log_loss),
        "baseline_log_loss": float(baseline_log_loss),
        "log_loss_improvement": float(baseline_log_loss - model_log_loss),
        "on_base_brier_score": float(
            brier_score_loss(observed_on_base, on_base_probability)
        ),
        "feature_count": len(MATCHUP_FEATURES),
        "features": MATCHUP_FEATURES,
    }
    return MatchupTrainingResult(pipeline=pipeline, metrics=metrics, calibration=calibration)
