"""Deterministic, traceable explanation templates."""

from __future__ import annotations

from typing import Any

import numpy as np


def candidate_reasons(
    candidate: dict[str, Any],
    pool: list[dict[str, Any]],
) -> list[str]:
    """Return up to three evidence-backed reasons relative to the candidate pool."""

    reasons: list[tuple[float, str]] = []
    median_k = float(np.median([float(value["pitcher_k_rate"]) for value in pool]))
    median_walk = float(np.median([float(value["pitcher_walk_rate"]) for value in pool]))
    median_woba = float(np.median([float(value["pitcher_woba"]) for value in pool]))
    median_rest = float(np.median([float(value["days_rest"]) for value in pool]))
    median_out = float(np.median([float(value["mean_projected_out_probability"]) for value in pool]))

    k_rate = float(candidate["pitcher_k_rate"])
    walk_rate = float(candidate["pitcher_walk_rate"])
    woba = float(candidate["pitcher_woba"])
    rest = float(candidate["days_rest"])
    out_probability = float(candidate["mean_projected_out_probability"])
    if out_probability > median_out + 0.005:
        reasons.append(
            (out_probability - median_out, "a stronger projected out rate against the next three hitters")
        )
    if k_rate > median_k + 0.005:
        reasons.append((k_rate - median_k, "a stronger league-pooled strikeout profile"))
    if walk_rate < median_walk - 0.003:
        reasons.append((median_walk - walk_rate, "better projected walk suppression"))
    if woba < median_woba - 0.003:
        reasons.append((median_woba - woba, "a lower league-pooled wOBA allowed profile"))
    if rest > median_rest:
        reasons.append(((rest - median_rest) / 100.0, "more rest before the decision"))
    if not reasons:
        return ["the best combined projected outcome distribution under the shared assumptions"]
    return [text for _, text in sorted(reasons, reverse=True)[:3]]
