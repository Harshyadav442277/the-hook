"""Method, validation, and limitations for THE HOOK."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from src.config import ARTIFACTS_DIR, PHASE2_END_DATE, PHASE2_START_DATE, PROFILE_PRIOR_WEIGHT, SIMULATION_COUNT
from src.ui.charts import calibration_figure
from src.ui.theme import apply_theme


st.set_page_config(page_title="How It Works · THE HOOK", page_icon="⚾", layout="wide")
apply_theme()
with st.sidebar:
    try:
        st.page_link("app.py", label="Decision Room", icon="⚾")
        st.page_link("pages/1_How_It_Works.py", label="How It Works", icon="📊")
    except KeyError:
        # Streamlit's isolated AppTest runner has no multipage registry. The
        # production app always does, so this branch is test-harness-only.
        pass

metrics = json.loads((ARTIFACTS_DIR / "metrics.json").read_text(encoding="utf-8"))
calibration = pd.read_parquet(ARTIFACTS_DIR / "calibration.parquet")
matchup = metrics["matchup"]
state = metrics["win_expectancy"]

st.markdown('<div class="hook-eyebrow">METHOD & VALIDATION</div>', unsafe_allow_html=True)
st.title("How THE HOOK works")
st.write(
    "THE HOOK compares relievers using only information available before each decision, "
    "projects four plate-appearance outcomes, and evaluates 2,000 shared-assumption simulations."
)

columns = st.columns(3)
for column, number, title, copy in zip(
    columns,
    ("01", "02", "03"),
    ("Profile", "Project", "Simulate"),
    (
        "Build prior-only pitcher, batter, handedness, and rest features.",
        "Estimate Out, Walk/HBP, Single, and Extra-base probabilities.",
        "Run the next three hitters and score terminal states with win expectancy.",
    ),
):
    with column:
        st.markdown(
            f'<div class="method-step"><span class="num">{number}</span><h3>{title}</h3><p>{copy}</p></div>',
            unsafe_allow_html=True,
        )

st.subheader("Data and point-in-time discipline")
st.write(
    f"The build uses {PHASE2_START_DATE} through {PHASE2_END_DATE} Statcast data. "
    f"Player rates are shrunk toward fixed league priors with a {PROFILE_PRIOR_WEIGHT:.0f}-PA prior, "
    "and every scenario uses the latest profile snapshot strictly before its game date."
)
st.info(
    f"Chronological validation: {matchup['train_date_min']}–{matchup['train_date_max']} train; "
    f"{matchup['holdout_date_min']}–{matchup['holdout_date_max']} holdout."
)

st.subheader("Holdout validation")
metric_columns = st.columns(3)
metric_columns[0].metric("Multiclass log loss", f"{matchup['multiclass_log_loss']:.4f}")
metric_columns[1].metric("League baseline", f"{matchup['baseline_log_loss']:.4f}")
metric_columns[2].metric("On-base Brier score", f"{matchup['on_base_brier_score']:.4f}")
st.write(
    "Lower is better. The regularized matchup model improves modestly over the league-rate "
    "baseline, supporting relative comparisons—not strong claims about exact outcomes."
)
st.plotly_chart(calibration_figure(calibration), use_container_width=True, config={"displayModeBar": False})
st.caption("Each point groups holdout plate appearances by predicted on-base probability.")

st.subheader("Short-horizon simulation")
st.write(
    f"For each candidate, THE HOOK samples up to three hitters across {SIMULATION_COUNT:,} "
    "deterministic trials. Outs, forced walks, singles, and pooled extra-base-hit subtypes "
    "advance a common game state. A chronological logistic state model estimates win "
    f"expectancy (holdout log loss {state['log_loss']:.4f} vs {state['baseline_log_loss']:.4f} baseline)."
)

st.subheader("Limitations")
st.warning(
    "These are transparent comparative estimates, not causal proof. Availability, injury, "
    "warm-up status, defense, pitch sequencing, and richer baserunning are simplified. "
    "Small samples are pooled, and absolute win probability remains approximate."
)
