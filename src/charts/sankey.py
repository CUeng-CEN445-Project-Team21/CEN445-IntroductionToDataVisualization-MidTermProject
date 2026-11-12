"""
3. ADVANCED: Sankey Diagram (HT Sonucu -> FT Sonucu Akışı & Comeback Analizi)
Insight: Visualizes match momentum transitions (e.g. halftime deficit to win).
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.theme import COLOR_PALETTE, THEME_TEMPLATE


def _classify_flow(htr: str, ftr: str) -> tuple[str, str]:
    """Return (flow_label, rgba_color) for a Half-Time -> Full-Time transition."""
    if htr == 'A' and ftr == 'H':
        return "Home Comeback", "rgba(16, 185, 129, 0.75)"   # Emerald comeback
    if htr == 'H' and ftr == 'A':
        return "Away Comeback", "rgba(244, 63, 94, 0.75)"    # Rose away comeback
    if htr == 'H' and ftr == 'H':
        return "Home Lead Held", "rgba(59, 130, 246, 0.40)"  # Blue
    if htr == 'D' and ftr == 'D':
        return "Draw Held", "rgba(245, 158, 11, 0.35)"       # Amber
    if htr == 'A' and ftr == 'A':
        return "Away Lead Held", "rgba(239, 68, 68, 0.35)"   # Red
    return "Momentum Shift", "rgba(148, 163, 184, 0.25)"


def build(df: pd.DataFrame) -> go.Figure:
    # Nodes:
    # 0: HT Home Lead, 1: HT Draw, 2: HT Away Lead
    # 3: FT Home Win, 4: FT Draw, 5: FT Away Win
    flows = df.groupby(['htr', 'ftr']).size().reset_index(name='count')
    total_matches = max(int(flows['count'].sum()), 1)
    ht_totals = flows.groupby('htr')['count'].transform('sum').clip(lower=1)
    flows['pct_ht'] = (flows['count'] / ht_totals * 100).round(1)
    flows['pct_total'] = (flows['count'] / total_matches * 100).round(1)

    node_labels = [
        "HT: Home Lead", "HT: Draw", "HT: Away Lead",
        "FT: Home Win", "FT: Draw", "FT: Away Win"
    ]
    node_colors = [
        COLOR_PALETTE['home'], COLOR_PALETTE['draw'], COLOR_PALETTE['away'],
        "#2563EB", "#D97706", "#DC2626"
    ]

    source_idx = {'H': 0, 'D': 1, 'A': 2}
    target_idx = {'H': 3, 'D': 4, 'A': 5}

    sources = [source_idx[r['htr']] for _, r in flows.iterrows()]
    targets = [target_idx[r['ftr']] for _, r in flows.iterrows()]
    values = flows['count'].tolist()

    flow_meta = [_classify_flow(r['htr'], r['ftr']) for _, r in flows.iterrows()]
    link_labels = [m[0] for m in flow_meta]
    link_colors = [m[1] for m in flow_meta]
    link_customdata = list(zip(link_labels, flows['pct_ht'].tolist(), flows['pct_total'].tolist()))

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=18,
            thickness=22,
            line=dict(color="rgba(15, 23, 42, 0.6)", width=0.6),
            label=node_labels,
            color=node_colors,
            hovertemplate="<b>%{label}</b><br>Matches: <b>%{value:,}</b><extra></extra>",
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors,
            customdata=link_customdata,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "%{source.label} → %{target.label}<br><br>"
                "Matches: <b>%{value:,}</b><br>"
                "Share of HT State: <b>%{customdata[1]:.1f}%</b><br>"
                "Share of All Matches: <b>%{customdata[2]:.1f}%</b>"
                "<extra></extra>"
            ),
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
