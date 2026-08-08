"""Reusable Decision Room components."""

from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st


def scenario_label(scenario: dict[str, Any]) -> str:
    occupied = [name for name, present in scenario["bases"].items() if present]
    runners = "bases loaded" if len(occupied) == 3 else (
        "runners on " + " & ".join(value.title() for value in occupied)
        if occupied else "bases empty"
    )
    marker = "Flagship · " if scenario.get("is_flagship") else ""
    return (
        f"{marker}{scenario['fielding_team']} vs {scenario['batting_team']} · "
        f"{scenario['inning_half'].title()} {scenario['inning']} · {runners}"
    )


def _name(scenario: dict[str, Any], player_id: int) -> str:
    return str(scenario["display_names"].get(str(player_id), f"MLB #{player_id}"))


def render_situation(scenario: dict[str, Any]) -> None:
    occupied = [
        key.replace("first", "1B").replace("second", "2B").replace("third", "3B")
        for key, present in scenario["bases"].items()
        if present
    ]
    base_text = ", ".join(occupied) if occupied else "Empty"
    base_chips = "".join(
        f'<span class="base-chip {"on" if scenario["bases"][key] else ""}">{label}</span>'
        for key, label in (("third", "3B"), ("second", "2B"), ("first", "1B"))
    )
    current = escape(_name(scenario, int(scenario["current_pitcher_id"])))
    hitters = " · ".join(
        escape(_name(scenario, int(value))) for value in scenario["upcoming_batter_ids"]
    )
    field_score = (
        scenario["home_score"]
        if scenario["fielding_team"] == scenario["home_team"]
        else scenario["away_score"]
    )
    batting_score = (
        scenario["away_score"]
        if scenario["fielding_team"] == scenario["home_team"]
        else scenario["home_score"]
    )
    st.markdown(
        f"""
        <div class="situation-grid">
          <div class="situation-item"><span class="hook-label">Moment</span><b>{escape(scenario['inning_half'].title())} {scenario['inning']}</b></div>
          <div class="situation-item"><span class="hook-label">Score</span><b>{escape(scenario['fielding_team'])} {field_score}–{batting_score} {escape(scenario['batting_team'])}</b></div>
          <div class="situation-item"><span class="hook-label">Outs</span><b>{scenario['outs']} of 3</b></div>
          <div class="situation-item"><span class="hook-label">Runners: {base_text}</span><b>{base_chips}</b></div>
        </div>
        <div class="hook-card" style="margin-top:.8rem">
          <span class="hook-label">On the mound</span> <b>{current}</b><br>
          <span class="hook-label">Upcoming hitters</span> <b>{hitters}</b>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_decision_cards(
    scenario: dict[str, Any], ranking: list[dict[str, Any]]
) -> None:
    actual = next(item for item in ranking if item["is_actual_choice"])
    recommended = ranking[0]
    columns = st.columns(2, gap="large")
    with columns[0]:
        st.markdown(
            f"""<div class="hook-card actual"><span class="hook-label">Actual decision</span>
            <div class="hook-value">{escape(actual['candidate_name'])}</div>
            <div class="hook-wp">{actual['estimated_win_probability']:.1%} estimated WP</div>
            <p class="muted">What the manager chose</p></div>""",
            unsafe_allow_html=True,
        )
    with columns[1]:
        st.markdown(
            f"""<div class="hook-card recommended"><span class="hook-label">The Hook recommends</span>
            <div class="hook-value">{escape(recommended['candidate_name'])}</div>
            <div class="hook-wp">{recommended['estimated_win_probability']:.1%} estimated WP</div>
            <p class="muted">Model recommendation under shared assumptions</p></div>""",
            unsafe_allow_html=True,
        )
    delta = float(recommended["delta_vs_actual"]) * 100
    if recommended["is_actual_choice"]:
        message = "THE HOOK agrees with the call."
    elif delta < 0.5:
        message = "The leading choices are effectively tied under this model."
    else:
        message = f"The model estimates a +{delta:.1f}-percentage-point advantage."
    st.markdown(f'<div class="hook-delta">{escape(message)}</div>', unsafe_allow_html=True)
    st.caption("A comparative estimate—not the observed counterfactual outcome.")
    for reason in recommended["reasons"]:
        st.markdown(f"- {reason.capitalize()}.")
