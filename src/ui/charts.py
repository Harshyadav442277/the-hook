"""Plotly figures shared by both Streamlit pages."""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go


def ranking_figure(ranking: list[dict[str, Any]]) -> go.Figure:
    frame = pd.DataFrame(ranking).sort_values("estimated_win_probability")
    colors = [
        "#176B4D" if value else "#C74755" if actual else "#8B98A5"
        for value, actual in zip(frame["is_recommended"], frame["is_actual_choice"])
    ]
    labels = [
        "Recommended" if value else "Actual" if actual else "Alternative"
        for value, actual in zip(frame["is_recommended"], frame["is_actual_choice"])
    ]
    fig = go.Figure(
        go.Bar(
            x=frame["estimated_win_probability"],
            y=frame["candidate_name"],
            orientation="h",
            marker_color=colors,
            text=[f"{value:.1%} · {label}" for value, label in zip(frame["estimated_win_probability"], labels)],
            textposition="outside",
            hovertemplate="%{y}<br>Estimated WP: %{x:.1%}<extra></extra>",
        )
    )
    fig.update_layout(
        height=285,
        margin=dict(l=10, r=120, t=10, b=35),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#0B1F33"),
        xaxis=dict(range=[0, 1], tickformat=".0%", title="Estimated win probability", gridcolor="#E6EBEF"),
        yaxis=dict(title=None),
        showlegend=False,
    )
    return fig


def calibration_figure(calibration: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[0, 1], y=[0, 1], mode="lines", name="Perfect calibration",
            line=dict(color="#AAB4BE", dash="dash"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=calibration["mean_predicted"],
            y=calibration["observed_rate"],
            mode="lines+markers",
            name="Holdout bins",
            marker=dict(color="#176B4D", size=9),
            line=dict(color="#176B4D"),
            customdata=calibration["count"],
            hovertemplate="Predicted %{x:.1%}<br>Observed %{y:.1%}<br>Rows %{customdata:,}<extra></extra>",
        )
    )
    fig.update_layout(
        height=360,
        margin=dict(l=20, r=20, t=25, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="white",
        font=dict(color="#0B1F33"),
        xaxis=dict(title="Mean predicted on-base probability", tickformat=".0%", range=[0, 0.6]),
        yaxis=dict(title="Observed on-base rate", tickformat=".0%", range=[0, 0.6]),
        legend=dict(orientation="h", y=1.12),
    )
    return fig
