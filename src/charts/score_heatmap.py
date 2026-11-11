"""
7. ANALYTICAL: Exact Scoreline Heatmap
Insight: Most frequent goal combinations (Home Goals vs Away Goals).
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.theme import THEME_TEMPLATE


def build(df: pd.DataFrame) -> go.Figure:
    sub = df[(df['fthg'] <= 5) & (df['ftag'] <= 5)]
    score_matrix = pd.crosstab(sub['fthg'], sub['ftag'])

    fig = px.imshow(
        score_matrix,
        labels=dict(x="Away Goals", y="Home Goals", color="Match Frequency"),
        x=score_matrix.columns,
        y=score_matrix.index,
        color_continuous_scale="Magma",
        text_auto=True,
        title="🔥 7. Exact Scoreline Distribution Matrix (0-5 Goals)"
    )

    fig.update_layout(
        template=THEME_TEMPLATE,
        height=420,
        margin=dict(l=10, r=10, t=50, b=10)
    )
    return fig


def render(df: pd.DataFrame):
    st.plotly_chart(build(df), width="stretch")
