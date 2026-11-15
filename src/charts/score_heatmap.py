"""
7. ANALYTICAL: Exact Scoreline Heatmap
Insight: Most frequent goal combinations (Home Goals vs Away Goals).
Includes interactive metric toggle (Count vs Percentage) and result zone filters.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.theme import THEME_TEMPLATE


def build(df: pd.DataFrame, view_mode: str = "Count", zone_filter: str = "All Scores", max_goals: int = 5) -> go.Figure:
    sub = df[(df['fthg'] <= max_goals) & (df['ftag'] <= max_goals)].copy()
    total_valid = len(sub)
    if total_valid == 0:
        total_valid = 1

    # Base frequency crosstab
    score_matrix = pd.crosstab(sub['fthg'], sub['ftag'])
    
    # Reindex to ensure complete square matrix 0..max_goals
    all_goals = list(range(max_goals + 1))
    score_matrix = score_matrix.reindex(index=all_goals, columns=all_goals, fill_value=0)

    # Percentage matrix
    pct_matrix = (score_matrix / total_valid * 100).round(2)

    # Filter by result zone if requested
    filtered_matrix = score_matrix.copy()
    filtered_pct = pct_matrix.copy()

    for h in all_goals:
        for a in all_goals:
            match_zone = "Other"
            if h == a:
                match_zone = "Draws Only"
            elif h > a:
                match_zone = "Home Wins Only"
            elif a > h:
                match_zone = "Away Wins Only"

            is_under = (h + a) < 2.5

            if zone_filter == "Draws Only" and match_zone != "Draws Only":
                filtered_matrix.loc[h, a] = np.nan
                filtered_pct.loc[h, a] = np.nan
            elif zone_filter == "Home Wins Only" and match_zone != "Home Wins Only":
                filtered_matrix.loc[h, a] = np.nan
                filtered_pct.loc[h, a] = np.nan
            elif zone_filter == "Away Wins Only" and match_zone != "Away Wins Only":
                filtered_matrix.loc[h, a] = np.nan
                filtered_pct.loc[h, a] = np.nan
            elif zone_filter == "Under 2.5 Only" and not is_under:
                filtered_matrix.loc[h, a] = np.nan
                filtered_pct.loc[h, a] = np.nan

    display_data = filtered_pct if view_mode == "Percentage (%)" else filtered_matrix

    # Custom text for cells
    text_data = []
    for h in all_goals:
        row_text = []
        for a in all_goals:
            c = score_matrix.loc[h, a]
            p = pct_matrix.loc[h, a]
            if np.isnan(display_data.loc[h, a]):
                row_text.append("")
            elif view_mode == "Percentage (%)":
                row_text.append(f"{p:.1f}%")
            else:
                row_text.append(f"{int(c):,}")
        text_data.append(row_text)

    # Custom hover text
    hover_text = []
    for h in all_goals:
        row_hover = []
        for a in all_goals:
            c = score_matrix.loc[h, a]
            p = pct_matrix.loc[h, a]
            outcome = "Draw" if h == a else ("Home Win" if h > a else "Away Win")
            u_o = "Under 2.5" if (h + a) < 2.5 else "Over 2.5"
            row_hover.append(
                f"<b>Score: {h} - {a}</b><br>"
                f"Matches: <b>{int(c):,}</b> ({p:.2f}% of all matches)<br>"
                f"Outcome: {outcome}<br>"
                f"Total Goals: {h + a} ({u_o})"
            )
        hover_text.append(row_hover)

    fig = go.Figure(data=go.Heatmap(
        z=display_data.values,
        x=[f"{a} Away" for a in all_goals],
        y=[f"{h} Home" for h in all_goals],
        text=text_data,
        texttemplate="%{text}",
        textfont=dict(size=13),
        hoverinfo="text",
        hovertext=hover_text,
        colorscale="Magma",
        showscale=True,
        colorbar=dict(
            title="%" if view_mode == "Percentage (%)" else "Matches",
            thickness=12,
            len=0.9
        )
    ))

    fig.update_layout(
        title=f"7. Exact Scoreline Distribution Matrix ({zone_filter})",
        template=THEME_TEMPLATE,
        height=430,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(title="Away Team Goals", side="bottom"),
        yaxis=dict(title="Home Team Goals", autorange="reversed")
    )
    return fig


def render(df: pd.DataFrame):
    c1, c2 = st.columns([1, 1])
    with c1:
        view_mode = st.pills(
            "Display Value",
            options=["Count", "Percentage (%)"],
            default="Count",
            key="score_heatmap_view_mode"
        )
    with c2:
        zone_filter = st.selectbox(
            "Highlight Zone",
            options=["All Scores", "Draws Only", "Home Wins Only", "Away Wins Only", "Under 2.5 Only"],
            key="score_heatmap_zone_filter"
        )

    mode = view_mode if view_mode else "Count"
    st.plotly_chart(build(df, view_mode=mode, zone_filter=zone_filter), width="stretch")
