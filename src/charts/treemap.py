"""
2. ADVANCED: Hierarchical Treemap (Lig -> Takım Hiyerarşisi)
Insight: Visualizes goal productivity and match volume across league hierarchies.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.theme import THEME_TEMPLATE


def build(df: pd.DataFrame) -> go.Figure:
    # Team level goals
    home_g = df.groupby(['league_name', 'home_team'])['fthg'].sum().reset_index()
    home_g.columns = ['league_name', 'team', 'goals']
    away_g = df.groupby(['league_name', 'away_team'])['ftag'].sum().reset_index()
    away_g.columns = ['league_name', 'team', 'goals']

    team_goals = pd.concat([home_g, away_g]).groupby(['league_name', 'team'])['goals'].sum().reset_index()

    # Wins calculation
    home_w = df[df['ftr'] == 'H'].groupby(['league_name', 'home_team']).size().reset_index(name='wins')
    home_w.columns = ['league_name', 'team', 'wins']
    away_w = df[df['ftr'] == 'A'].groupby(['league_name', 'away_team']).size().reset_index(name='wins')
    away_w.columns = ['league_name', 'team', 'wins']
    team_wins = pd.concat([home_w, away_w]).groupby(['league_name', 'team'])['wins'].sum().reset_index()

    merged = pd.merge(team_goals, team_wins, on=['league_name', 'team'], how='left').fillna(0)
    merged['goals'] = merged['goals'].astype(int)
    merged['wins'] = merged['wins'].astype(int)

    if merged.empty or merged['goals'].sum() == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No goals recorded under current filters.",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False, font=dict(size=14)
        )
        fig.update_layout(
            title="🌳 2. Goal Dominance & Wins Treemap (League & Team Hierarchy)",
            template=THEME_TEMPLATE,
            margin=dict(l=10, r=10, t=50, b=10),
            height=480,
        )
        return fig

    fig = px.treemap(
        merged,
        path=[px.Constant("All Selected Leagues"), 'league_name', 'team'],
        values='goals',
        color='wins',
        color_continuous_scale='Blues',
        title="🌳 2. Goal Dominance & Wins Treemap (League & Team Hierarchy)"
    )

    fig.update_traces(
        textinfo="label+value",
        tiling=dict(packing='squarify'),
        marker=dict(line=dict(width=1, color='rgba(15, 23, 42, 0.35)')),
        hovertemplate=(
            "<b>%{label}</b><br><br>"
            "Total Goals: <b>%{value:,}</b><br>"
            "Wins (Team / Avg): <b>%{color:.1f}</b><br>"
            "Share of Parent: <b>%{percentParent:.1%}</b>"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        template=THEME_TEMPLATE,
        coloraxis_colorbar=dict(
            title=dict(text="Wins"),
            thickness=14,
            len=0.85,
        ),
        margin=dict(l=10, r=10, t=50, b=10),
        height=480
    )
    return fig


def render(df: pd.DataFrame):
    st.plotly_chart(build(df), width="stretch")
