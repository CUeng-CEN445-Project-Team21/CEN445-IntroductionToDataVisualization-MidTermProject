"""
4. ADVANCED: Parallel Coordinates (Çok Boyutlu Bahis Oranları Analizi)
Insight: Unveils how bookmaker odds coordinates map into distinct match outcomes.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.theme import THEME_TEMPLATE


def build(df: pd.DataFrame, max_samples: int = 1500) -> go.Figure:
    sample_df = df.sample(min(len(df), max_samples), random_state=42).copy()

    # Encode result to numerical for coloring: Home=1, Draw=2, Away=3
    outcome_code = {'H': 1, 'D': 2, 'A': 3}
    sample_df['outcome_num'] = sample_df['ftr'].map(outcome_code)

    fig = go.Figure(data=go.Parcoords(
        line=dict(
            color=sample_df['outcome_num'],
            colorscale=[[0, '#3B82F6'], [0.5, '#F59E0B'], [1, '#EF4444']],
            showscale=True,
            colorbar=dict(
                title="Result",
                tickvals=[1, 2, 3],
                ticktext=["Home Win", "Draw", "Away Win"]
            )
        ),
        dimensions=[
            dict(range=[1, 10], label='Home Odds', values=sample_df['home_odds']),
            dict(range=[1, 8], label='Draw Odds', values=sample_df['draw_odds']),
            dict(range=[1, 12], label='Away Odds', values=sample_df['away_odds']),
            dict(range=[1, 4], label='Over 2.5 Odds', values=sample_df['over_25_odds'].fillna(2.0)),
            dict(range=[0, 8], label='Total Goals', values=sample_df['total_goals'])
        ]
    ))

    fig.update_layout(
        title="📈 4. Multi-Dimensional Betting Odds & Outcome Profile (Parallel Coordinates)",
        template=THEME_TEMPLATE,
        height=450,
        margin=dict(l=50, r=50, t=50, b=20)
    )
    return fig


def render(df: pd.DataFrame):
    st.plotly_chart(build(df), width="stretch")
