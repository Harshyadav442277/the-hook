"""THE HOOK — explainable MLB bullpen decision simulator."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from src.config import ARTIFACTS_DIR
from src.ui.charts import ranking_figure
from src.ui.components import render_decision_cards, render_situation, scenario_label
from src.ui.theme import apply_theme


st.set_page_config(page_title="THE HOOK", page_icon="⚾", layout="wide")
apply_theme()
with st.sidebar:
    st.page_link("app.py", label="Decision Room", icon="⚾")
    st.page_link("pages/1_How_It_Works.py", label="How It Works", icon="📊")


@st.cache_data(show_spinner=False)
def load_scenarios(path: str) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


try:
    scenarios = load_scenarios(str(ARTIFACTS_DIR / "runtime_scenarios.json"))
except Exception:
    st.error(
        "THE HOOK could not load its analysis artifacts. Rebuild them with "
        "`python scripts/build_runtime_artifacts.py`."
    )
    st.stop()

st.markdown('<div class="hook-eyebrow">MLB BULLPEN DECISION LAB</div>', unsafe_allow_html=True)
st.markdown('<div class="hook-title">THE HOOK</div>', unsafe_allow_html=True)
st.markdown('<div class="hook-tagline">Should the manager make the call?</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hook-subtitle">Compare a real bullpen decision with statistically projected alternatives in a high-leverage moment.</div>',
    unsafe_allow_html=True,
)

labels = {scenario_label(item): item for item in scenarios}
selected_label = st.selectbox("Choose a decision replay", list(labels), index=0)
scenario = labels[selected_label]
ranking = scenario["default_ranking"]

st.subheader("The situation")
render_situation(scenario)

st.subheader("Manager vs Model")
render_decision_cards(scenario, ranking)

st.subheader("Candidate ranking")
st.plotly_chart(ranking_figure(ranking), use_container_width=True, config={"displayModeBar": False})
table = [
    {
        "Rank": item["rank"],
        "Reliever": item["candidate_name"],
        "Estimated WP": f"{item['estimated_win_probability']:.1%}",
        "Δ vs actual": f"{item['delta_vs_actual'] * 100:+.1f} pp",
        "Expected runs": f"{item['expected_runs_allowed']:.2f}",
        "Status": "Recommended" if item["is_recommended"] else "Actual" if item["is_actual_choice"] else "Alternative",
    }
    for item in ranking
]
st.dataframe(table, hide_index=True, use_container_width=True)

st.subheader("Try another call")
candidate_by_name = {item["candidate_name"]: item for item in ranking}
recommended_name = ranking[0]["candidate_name"]
choice = st.selectbox(
    "What-if reliever",
    list(candidate_by_name),
    index=list(candidate_by_name).index(recommended_name),
    key=f"what_if_{scenario['scenario_id']}",
)
selected = candidate_by_name[choice]
evidence = next(
    item for item in scenario["candidate_evidence"] if item["candidate_id"] == selected["candidate_id"]
)
metric_columns = st.columns(4)
metric_columns[0].metric("Estimated WP", f"{selected['estimated_win_probability']:.1%}")
metric_columns[1].metric("Vs actual", f"{selected['delta_vs_actual'] * 100:+.1f} pp")
metric_columns[2].metric("Expected runs", f"{selected['expected_runs_allowed']:.2f}")
rest_unit = "day" if evidence["days_rest"] == 1 else "days"
metric_columns[3].metric(
    "Rest before decision", f"{evidence['days_rest']} {rest_unit}"
)
st.markdown(f"**{choice}** throws {evidence['pitcher_hand']} and had {evidence['pitcher_pa_before']:,} prior profile plate appearances.")
for reason in selected["reasons"]:
    st.markdown(f"- {reason.capitalize()}.")

with st.expander("Assumptions and limitations"):
    st.markdown(
        """
        - The horizon is at most the next three hitters and stops at the third out.
        - Base advancement uses the same simplified rules for every candidate.
        - Absolute win probability is approximate; relative choices share assumptions.
        - Player form, bullpen availability, and injury context are simplified.
        - Counterfactual estimates are associations, not proof of what would have happened.
        """
    )
    st.caption(
        f"Profiles use the latest snapshot strictly before {scenario['game_date']}. "
        f"Each candidate uses {ranking[0]['simulation_count']:,} deterministic simulations."
    )

st.divider()
st.caption("Data: MLB Statcast / Baseball Savant · Built for the AQX Sports Analytics Data Bowl 3.0")
