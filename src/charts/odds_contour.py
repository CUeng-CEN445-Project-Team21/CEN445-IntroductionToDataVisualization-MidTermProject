"""
6. ADVANCED: 2D Contour / Density Plot (Bahis Oranları Yoğunluk Yüzeyi)
Insight: Uncovers market odds clusters and identifies upset sweet-spots.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.theme import RESULT_COLORS, THEME_TEMPLATE


def build(df: pd.DataFrame) -> go.Figure:
    clean = df[(df['home_odds'] <= 6.0) & (df['away_odds'] <= 8.0)].copy()

    fig = px.density_contour(
        clean,
        x='home_odds',
        y='away_odds',
        color='result_label',
        color_discrete_map=RESULT_COLORS,
        title="🌌 6. Market Odds Density Landscape & Upset Clusters (2D Contour)"
    )

    fig.update_traces(contours_coloring="lines", line_width=1.5)
    fig.update_layout(
        template=THEME_TEMPLATE,
        xaxis_title="Home Closing Odds",
        yaxis_title="Away Closing Odds",
        height=450,
        margin=dict(l=10, r=10, t=50, b=10)
    )
    return fig


def render(df: pd.DataFrame):
    st.plotly_chart(build(df), width="stretch")
