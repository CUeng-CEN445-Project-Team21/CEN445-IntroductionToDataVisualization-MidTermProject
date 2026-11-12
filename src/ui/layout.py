"""
layout.py - What goes where on the page. This file is a map of the dashboard.

Each tab has a list of rows. A row is a list of modules drawn side by side
(one module = full width, two = two columns, ...). The string "---" draws a divider.
"""

from dataclasses import dataclass

import streamlit as st

from src.charts import (
    calibration_scatter, choropleth, league_goals_violin, network_graph,
    odds_contour, parallel_coordinates, sankey, score_heatmap, treemap,
)
from src.ml import classifier, clustering


@dataclass
class Tab:
    label: str
    heading: str
    insight: str
    rows: list


TABS = [
    Tab(
        label="🌍 1. League & Geography",
        heading="Geographical Landscape & League Hierarchies",
        insight="European leagues exhibit distinct goal profiles. Use the map to compare countries "
                "and the treemap to navigate team-level productivity.",
        rows=[
            [choropleth],                     # Chart 1: Necdet Özdemir
            [treemap, league_goals_violin],   # Chart 2: Necdet Özdemir | Chart 9: Celal Kadir Aydaş
        ],
    ),
    Tab(
        label="🌊 2. Match Momentum & Odds",
        heading="Match Flow Dynamics & Multi-Dimensional Odds Space",
        insight="Explore how halftime leads translate into fulltime victories via Sankey flow, "
                "and inspect multi-dimensional betting lines with Parallel Coordinates.",
        rows=[
            [sankey],                              # Chart 3: Necdet Özdemir
            [parallel_coordinates, odds_contour],  # Chart 4: Yusuf Semih Can | Chart 6: Yusuf Semih Can
        ],
    ),
    Tab(
        label="🔥 3. Scores & Team Networks",
        heading="Exact Score Matrix, Calibration & Team Dominance Network",
        insight="Visualizing the most frequent exact scoreline combinations, bookmaker probability "
                "efficiency, and head-to-head dominance networks.",
        rows=[
            [score_heatmap, calibration_scatter],  # Chart 7: Celal Kadir Aydaş | Chart 8: Celal Kadir Aydaş
            [network_graph],                       # Chart 5: Yusuf Semih Can
        ],
    ),
    Tab(
        label="🤖 4. Machine Learning & Predictive Insights",
        heading="Machine Learning Augmentation (Clustering & Classification)",
        insight="Machine learning models identify underlying tactical archetypes of teams and provide "
                "probability distributions for match outcomes based on market closing lines.",
        rows=[
            [clustering],
            "---",
            [classifier],
        ],
    ),
]


def render(df):
    for tab, container in zip(TABS, st.tabs([t.label for t in TABS])):
        with container:
            st.subheader(tab.heading)
            st.info(f"💡 **Analytical Insight:** {tab.insight}")
            for row in tab.rows:
                if row == "---":
                    st.write("---")
                    continue
                columns = st.columns(len(row)) if len(row) > 1 else [st.container()]
                for module, column in zip(row, columns):
                    with column:
                        module.render(df)
