"""
8. ANALYTICAL: Calibration Scatter Plot (Value Bet & Bookmaker Accuracy)
Insight: Implied probability vs observed win rate with calibration baseline.
Includes dynamic market selector (Home/Draw/Away), value detection coloring,
and interactive fair market confidence bands.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.theme import THEME_TEMPLATE, COLOR_PALETTE


def build(df: pd.DataFrame, market: str = "Home Win", show_band: bool = True, n_bins: int = 15) -> go.Figure:
    prob_col_map = {
        "Home Win": ("prob_home", "H"),
        "Draw": ("prob_draw", "D"),
        "Away Win": ("prob_away", "A")
    }
    prob_col, target_result = prob_col_map.get(market, ("prob_home", "H"))

    clean = df.dropna(subset=[prob_col, 'ftr']).copy()
    if clean.empty:
        return go.Figure()

    min_p = max(0.05, float(clean[prob_col].quantile(0.01)))
    max_p = min(0.95, float(clean[prob_col].quantile(0.99)))

    bins = np.linspace(min_p, max_p, n_bins + 1)
    clean['prob_bin'] = pd.cut(clean[prob_col], bins=bins)

    calib = clean.groupby('prob_bin', observed=False).agg(
        expected_prob=(prob_col, 'mean'),
        actual_win_rate=('ftr', lambda x: (x == target_result).mean()),
        match_count=('id', 'count')
    ).reset_index().dropna()

    # Filter out empty bins
    calib = calib[calib['match_count'] >= 5]
    if calib.empty:
        return go.Figure()

    # Calculate discrepancy
    calib['diff'] = calib['actual_win_rate'] - calib['expected_prob']

    # Classify pricing efficiency: Value vs Overpriced
    def classify_status(diff):
        if diff > 0.02:
            return "Value Bet (Bookmaker Underestimated)", "#10B981"  # Emerald Green
        elif diff < -0.02:
            return "Overpriced (Bookmaker Overestimated)", "#EF4444"  # Coral Red
        else:
            return "Fairly Priced (Efficient)", "#3B82F6"             # Balanced Blue

    status_color = [classify_status(d) for d in calib['diff']]
    calib['status'] = [s[0] for s in status_color]
    calib['color'] = [s[1] for s in status_color]

    fig = go.Figure()

    # 1. Fair Market Tolerance Band (±3%)
    if show_band:
        line_x = np.linspace(min_p, max_p, 50)
        upper_band = np.clip(line_x + 0.03, 0, 1)
        lower_band = np.clip(line_x - 0.03, 0, 1)

        fig.add_trace(go.Scatter(
            x=line_x, y=upper_band,
            mode='lines',
            line=dict(width=0),
            hoverinfo='none',
            showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=line_x, y=lower_band,
            mode='lines',
            fill='tonexty',
            fillcolor='rgba(59, 130, 246, 0.12)',
            line=dict(width=0),
            name='±3% Fair Efficiency Band',
            hoverinfo='none'
        ))

    # 2. Perfect calibration 45-degree reference line
    fig.add_trace(go.Scatter(
        x=[min_p, max_p], y=[min_p, max_p],
        mode='lines',
        name='Perfect 1:1 Calibration',
        line=dict(dash='dash', color='#94A3B8', width=2)
    ))

    # 3. Observed Market Points
    hover_texts = [
        f"<b>Market: {market}</b><br>"
        f"Implied Probability (Odds): <b>{exp:.1%}</b><br>"
        f"Actual Realized Win Rate: <b>{act:.1%}</b><br>"
        f"Gap: <b>{diff:+.1%}</b><br>"
        f"Pricing: <i>{status}</i><br>"
        f"Sample Size: <b>{int(cnt):,} matches</b>"
        for exp, act, diff, status, cnt in zip(
            calib['expected_prob'], calib['actual_win_rate'],
            calib['diff'], calib['status'], calib['match_count']
        )
    ]

    fig.add_trace(go.Scatter(
        x=calib['expected_prob'],
        y=calib['actual_win_rate'],
        mode='markers+lines',
        name='Observed Market Outcome',
        line=dict(color='rgba(148, 163, 184, 0.4)', width=1.5),
        marker=dict(
            size=np.clip(calib['match_count'] / 25 + 7, 7, 24),
            color=calib['color'],
            line=dict(width=1.5, color='#FFFFFF')
        ),
        text=hover_texts,
        hoverinfo='text'
    ))

    # Overall calibration error metric
    mean_gap = (calib['diff'].abs()).mean() * 100
    fig.add_annotation(
        text=f"Avg Market Discrepancy: ±{mean_gap:.1f}%",
        xref="paper", yref="paper",
        x=0.03, y=0.95,
        showarrow=False,
        bgcolor="rgba(30, 41, 59, 0.8)",
        bordercolor="#334155",
        borderwidth=1,
        font=dict(size=11, color="#94A3B8")
    )

    fig.update_layout(
        title=f"8. Market Efficiency & Calibration ({market})",
        xaxis=dict(title=f"Bookmaker Implied Probability ({market})", tickformat=".0%"),
        yaxis=dict(title=f"Empirical Win Rate ({market})", tickformat=".0%"),
        template=THEME_TEMPLATE,
        height=430,
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def render(df: pd.DataFrame):
    c1, c2 = st.columns([1, 1])
    with c1:
        market = st.pills(
            "Market Outcome",
            options=["Home Win", "Draw", "Away Win"],
            default="Home Win",
            key="calibration_market_outcome"
        )
    with c2:
        show_band = st.checkbox(
            "Show ±3% Fair Efficiency Band",
            value=True,
            key="calibration_show_band"
        )

    selected_market = market if market else "Home Win"
    st.plotly_chart(build(df, market=selected_market, show_band=show_band), width="stretch")
