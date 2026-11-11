"""
8. ANALYTICAL: Calibration Scatter Plot (Value Bet & Bookmaker Accuracy)
Insight: Implied probability vs observed win rate with calibration baseline.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.theme import THEME_TEMPLATE


def build(df: pd.DataFrame) -> go.Figure:
    clean = df.dropna(subset=['prob_home', 'ftr']).copy()
    clean['prob_bin'] = pd.cut(clean['prob_home'], bins=np.linspace(0.1, 0.9, 17))

    calib = clean.groupby('prob_bin', observed=False).agg(
        expected_prob=('prob_home', 'mean'),
        actual_win_rate=('ftr', lambda x: (x == 'H').mean()),
        match_count=('id', 'count')
    ).reset_index().dropna()

    fig = go.Figure()

    # Perfect calibration 45-deg line
    fig.add_trace(go.Scatter(
        x=[0.1, 0.9], y=[0.1, 0.9],
        mode='lines',
        name='Perfect Calibration (1:1)',
        line=dict(dash='dash', color='#64748B', width=2)
    ))

    # Observed data points
    fig.add_trace(go.Scatter(
        x=calib['expected_prob'],
        y=calib['actual_win_rate'],
        mode='markers+lines',
        name='Observed Market Win Rate',
        marker=dict(
            size=calib['match_count'] / 25 + 6,
            color='#10B981',
            line=dict(width=1.5, color='#FFFFFF')
        ),
        text=[f"Matches: {c}<br>Expected: {e:.1%}<br>Actual: {a:.1%}"
              for c, e, a in zip(calib['match_count'], calib['expected_prob'], calib['actual_win_rate'])],
        hoverinfo='text'
    ))

    fig.update_layout(
        title="🎯 8. Market Efficiency & Calibration (Expected vs Actual Win Rate)",
        xaxis_title="Implied Probability (1 / Fair Odds)",
        yaxis_title="Empirical Win Rate",
        template=THEME_TEMPLATE,
        height=420,
        margin=dict(l=10, r=10, t=50, b=10)
    )
    return fig


def render(df: pd.DataFrame):
    st.plotly_chart(build(df), width="stretch")
