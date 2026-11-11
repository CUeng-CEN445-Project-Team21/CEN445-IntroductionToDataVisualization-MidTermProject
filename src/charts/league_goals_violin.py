"""
9. ANALYTICAL: League Goal Distribution (Violin & Box Plot with Outliers)
Insight: Detects variance, goal inflation and extreme high-scoring outliers.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.theme import THEME_TEMPLATE


def build(df: pd.DataFrame) -> go.Figure:
    fig = px.violin(
        df,
        x='league_name',
        y='total_goals',
        color='league_name',
        box=True,
        points='outliers',
        hover_data=['home_team', 'away_team', 'match_date'],
        title="🎻 9. League Total Goal Distributions & Outlier Matches"
    )

    fig.update_layout(
        template=THEME_TEMPLATE,
        showlegend=False,
        xaxis_title="League",
        yaxis_title="Total Goals in Match",
        height=450,
        margin=dict(l=10, r=10, t=50, b=10)
    )
    return fig


def render(df: pd.DataFrame):
    st.plotly_chart(build(df), width="stretch")
