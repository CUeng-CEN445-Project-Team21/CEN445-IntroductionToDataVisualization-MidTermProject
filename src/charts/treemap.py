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

    fig = px.treemap(
        merged,
        path=[px.Constant("All Selected Leagues"), 'league_name', 'team'],
        values='goals',
        color='wins',
        color_continuous_scale='Blues',
        hover_data={'goals': True, 'wins': True},
        title="🌳 2. Goal Dominance & Wins Treemap (League & Team Hierarchy)"
    )

    fig.update_layout(
        template=THEME_TEMPLATE,
        margin=dict(l=10, r=10, t=50, b=10),
        height=500
    )
    return fig


def render(df: pd.DataFrame):
    st.plotly_chart(build(df), width="stretch")
