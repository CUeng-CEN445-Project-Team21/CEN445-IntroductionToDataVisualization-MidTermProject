"""
layout.py - What goes where on the page. This file is a map of the dashboard.

The page has two tabs:
  * Visual Analysis - the nine charts, split into three segments (one per team member).
                      A segmented control at the top picks which segment is shown.
  * Machine Learning - the clustering and classification models.

Each segment has a list of rows. A row is a list of modules drawn side by side
(one module = full width, two = two columns, ...). The string "---" draws a divider.
"""

from dataclasses import dataclass

import streamlit as st

from src.charts import (
    calibration_scatter, choropleth, league_goals_violin, network_graph,
    parallel_coordinates, sankey, score_heatmap, season_bubbles, treemap,
)
from src.ml import classifier, clustering


@dataclass
class Segment:
    label: str      # shown on the segmented control
    heading: str
    insight: str
    rows: list


CHART_SEGMENTS = [
    Segment(
        label="Charts 1–3 · League & Momentum",
        heading="Geographical Landscape, League Hierarchies & Match Momentum",
        insight="Compare countries on the map, drill into team-level productivity with the treemap, "
                "and follow how halftime leads turn into fulltime results in the Sankey flow.",
        rows=[
            [choropleth],        # Chart 1: Necdet Özdemir
            [treemap, sankey],   # Chart 2: Necdet Özdemir | Chart 3: Necdet Özdemir
        ],
    ),
    Segment(
        label="Charts 4–6 · Teams & Seasons",
        heading="Team Profiles, Head-to-Head Network & Season Trends",
        insight="Compare every team's full statistical profile, see who beats whom among a league's "
                "top teams, and watch whether each league's trends hold from August to May.",
        rows=[
            [parallel_coordinates],           # Chart 4: Yusuf Semih Can
            [network_graph, season_bubbles],  # Chart 5: Yusuf Semih Can | Chart 6: Yusuf Semih Can
        ],
    ),
    Segment(
        label="Charts 7–9 · Scores & Goals",
        heading="Exact Score Matrix, Market Calibration & Goal Distributions",
        insight="See the most frequent exact scorelines, how well bookmaker probabilities match "
                "reality, and how goal output is distributed in each league.",
        rows=[
            [score_heatmap, calibration_scatter],  # Chart 7: Celal Kadir Aydaş | Chart 8: Celal Kadir Aydaş
            [league_goals_violin],                 # Chart 9: Celal Kadir Aydaş
        ],
    ),
]

ML_SEGMENT = Segment(
    label="Machine Learning",
    heading="Machine Learning Augmentation (Clustering & Classification)",
    insight="Machine learning models identify underlying tactical archetypes of teams and provide "
            "probability distributions for match outcomes based on market closing lines.",
    rows=[
        [clustering],
        "---",
        [classifier],
    ],
)


def _draw_segment(segment: Segment, df):
    st.markdown(f'<div class="section-kicker">{segment.label}</div>', unsafe_allow_html=True)
    st.subheader(segment.heading, anchor=False)
    st.caption(segment.insight)
    for row in segment.rows:
        if row == "---":
            st.divider()
            continue
        for module, column in zip(row, st.columns(len(row))):
            with column, st.container(border=True):
                module.render(df)


def render(df):
    charts_tab, ml_tab = st.tabs([":material/insights: Visual Analysis", ":material/hub: Machine Learning"])

    with charts_tab:
        labels = [s.label for s in CHART_SEGMENTS]
        choice = st.segmented_control(
            "Chart group",
            options=labels,
            default=labels[0],
            key="layout_chart_segment",
            label_visibility="collapsed",
            width="stretch",
        )
        # Clicking the active segment again deselects it; fall back to the first one.
        segment = CHART_SEGMENTS[labels.index(choice)] if choice else CHART_SEGMENTS[0]
        _draw_segment(segment, df)

    with ml_tab:
        _draw_segment(ML_SEGMENT, df)
