"""
3. ADVANCED: Sankey Diagram (HT Sonucu -> FT Sonucu Akışı & Comeback Analizi)
Insight: Visualizes match momentum transitions (e.g. halftime deficit to win).
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.theme import THEME_TEMPLATE


def build(df: pd.DataFrame) -> go.Figure:
    # Nodes:
    # 0: HT Home Win, 1: HT Draw, 2: HT Away Win
    # 3: FT Home Win, 4: FT Draw, 5: FT Away Win
    flows = df.groupby(['htr', 'ftr']).size().reset_index(name='count')

    node_labels = [
        "HT: Home Lead", "HT: Draw", "HT: Away Lead",
        "FT: Home Win", "FT: Draw", "FT: Away Win"
    ]
    node_colors = [
        "#3B82F6", "#F59E0B", "#EF4444",
        "#2563EB", "#D97706", "#DC2626"
    ]

    source_idx = {'H': 0, 'D': 1, 'A': 2}
    target_idx = {'H': 3, 'D': 4, 'A': 5}

    sources = [source_idx[r['htr']] for _, r in flows.iterrows()]
    targets = [target_idx[r['ftr']] for _, r in flows.iterrows()]
    values = flows['count'].tolist()

    # Flow colors: highlight comebacks with vibrant colors
    link_colors = []
    for _, r in flows.iterrows():
        if r['htr'] == 'A' and r['ftr'] == 'H':
            link_colors.append("rgba(16, 185, 129, 0.7)")  # Emerald comeback
        elif r['htr'] == 'H' and r['ftr'] == 'A':
            link_colors.append("rgba(244, 63, 94, 0.7)")   # Rose away comeback
        elif r['htr'] == r['ftr']:
            link_colors.append("rgba(59, 130, 246, 0.35)")
        else:
            link_colors.append("rgba(148, 163, 184, 0.25)")

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=18,
            thickness=22,
            line=dict(color="black", width=0.5),
            label=node_labels,
            color=node_colors
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors
        )
    )])

    fig.update_layout(
        title="🌊 3. Half-Time to Full-Time Result Momentum (Sankey Flow)",
        template=THEME_TEMPLATE,
        height=450,
        margin=dict(l=10, r=10, t=50, b=10)
    )
    return fig


def render(df: pd.DataFrame):
    st.plotly_chart(build(df), width="stretch")
