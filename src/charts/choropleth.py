"""
1. ADVANCED: Geographical Choropleth Map (Avrupa Haritası)
Insight: Shows average goals per match and home advantage across European leagues.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.theme import THEME_TEMPLATE


def build(df: pd.DataFrame) -> go.Figure:
    country_stats = df.groupby(['country_iso3', 'country', 'league_name']).agg(
        total_matches=('id', 'count'),
        avg_goals=('total_goals', 'mean'),
        home_win_pct=('ftr', lambda x: (x == 'H').mean() * 100),
        draw_pct=('ftr', lambda x: (x == 'D').mean() * 100),
        away_win_pct=('ftr', lambda x: (x == 'A').mean() * 100)
    ).reset_index()

    country_stats['avg_goals'] = country_stats['avg_goals'].round(2)
    country_stats['home_win_pct'] = country_stats['home_win_pct'].round(1)

    fig = px.choropleth(
        country_stats,
        locations='country_iso3',
        color='avg_goals',
        hover_name='country',
        hover_data={
            'country_iso3': False,
            'league_name': True,
            'total_matches': True,
            'avg_goals': ':.2f',
            'home_win_pct': ':.1f%'
        },
        labels={'avg_goals': 'Avg Goals / Match', 'league_name': 'League'},
        color_continuous_scale='Viridis',
        scope='europe',
        title="🌍 1. European League Landscape: Average Goals & Home Advantage"
    )

    fig.update_layout(
        template=THEME_TEMPLATE,
        geo=dict(
            bgcolor='rgba(0,0,0,0)',
            showcoastlines=True,
            showcountries=True,
            showland=True,
            landcolor='rgba(148, 163, 184, 0.25)',   # neutral slate, readable in light and dark
            lakecolor='rgba(0,0,0,0)',
            projection_type='natural earth'
        ),
        margin=dict(l=10, r=10, t=50, b=10),
        height=450
    )
    return fig


def render(df: pd.DataFrame):
    st.plotly_chart(build(df), width="stretch")
