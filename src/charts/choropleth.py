"""
1. ADVANCED: Geographical Choropleth Map (Avrupa Haritası)
Insight: Shows average goals per match and home advantage across European leagues.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.theme import THEME_TEMPLATE

# Visual label anchors (lat, lon) kept centered on each league's primary territory
COUNTRY_LABEL_COORDS = {
    'GBR': (52.8, -1.6),
    'FRA': (46.6, 2.3),
    'DEU': (51.1, 10.4),
    'ITA': (42.8, 12.6),
    'NLD': (52.3, 5.5),
    'PRT': (39.6, -8.3),
    'TUR': (39.0, 35.2),
    'ESP': (40.2, -3.7),
    'BEL': (50.6, 4.6),
    'GRC': (39.2, 22.0),
}


def _label_text_colors(values: pd.Series) -> list[str]:
    """Choose dark or white text per country for contrast against the Viridis scale."""
    v_min, v_max = values.min(), values.max()
    if pd.isna(v_min) or v_max == v_min:
        return ['#FFFFFF'] * len(values)
    norm = (values - v_min) / (v_max - v_min)
    return ['#0F172A' if t >= 0.58 else '#FFFFFF' for t in norm]


def build(df: pd.DataFrame) -> go.Figure:
    country_stats = df.groupby(['country_iso3', 'country', 'league_name']).agg(
        total_matches=('id', 'count'),
        avg_goals=('total_goals', 'mean'),
        home_win_pct=('ftr', lambda x: (x == 'H').mean() * 100),
        draw_pct=('ftr', lambda x: (x == 'D').mean() * 100),
        away_win_pct=('ftr', lambda x: (x == 'A').mean() * 100),
        over_25_pct=('is_over_25', lambda x: x.mean() * 100),
    ).reset_index()

    country_stats['avg_goals'] = country_stats['avg_goals'].round(2)

    fig = px.choropleth(
        country_stats,
        locations='country_iso3',
        color='avg_goals',
        hover_name='country',
        custom_data=[
            'league_name',
            'total_matches',
            'home_win_pct',
            'draw_pct',
            'away_win_pct',
            'over_25_pct',
        ],
        labels={'avg_goals': 'Avg Goals / Match'},
        color_continuous_scale='Viridis',
        scope='world',
        title="🌍 1. European League Landscape: Average Goals & Home Advantage"
    )

    fig.update_traces(
        selector=dict(type='choropleth'),
        marker_line_color='rgba(255, 255, 255, 0.55)',
        marker_line_width=1.1,
        hovertemplate=(
            "<b>%{hovertext} — %{customdata[0]}</b><br><br>"
            "Matches: <b>%{customdata[1]:,}</b><br>"
            "Avg Goals / Match: <b>%{z:.2f}</b><br>"
            "Over 2.5 Goals: <b>%{customdata[5]:.1f}%</b><br>"
            "Home / Draw / Away: <b>%{customdata[2]:.1f}% / %{customdata[3]:.1f}% / %{customdata[4]:.1f}%</b>"
            "<extra></extra>"
        ),
    )

    # Overlay clean avg-goal value labels so every country is readable at a glance
    labeled = country_stats[country_stats['country_iso3'].isin(COUNTRY_LABEL_COORDS)].copy()
    if not labeled.empty:
        labeled['lat'] = labeled['country_iso3'].map(lambda c: COUNTRY_LABEL_COORDS[c][0])
        labeled['lon'] = labeled['country_iso3'].map(lambda c: COUNTRY_LABEL_COORDS[c][1])
        fig.add_trace(go.Scattergeo(
            lat=labeled['lat'],
            lon=labeled['lon'],
            text=[f"<b>{v:.2f}</b>" for v in labeled['avg_goals']],
            mode='text',
            textfont=dict(
                size=11,
                color=_label_text_colors(labeled['avg_goals']),
            ),
            hoverinfo='skip',
            showlegend=False,
        ))

    fig.update_layout(
        template=THEME_TEMPLATE,
        coloraxis_colorbar=dict(
            title=dict(text="Avg Goals"),
            thickness=14,
            len=0.82,
            tickformat=".2f",
        ),
        geo=dict(
            bgcolor='rgba(0,0,0,0)',
            showcoastlines=True,
            coastlinecolor='rgba(148, 163, 184, 0.45)',
            showcountries=True,
            countrycolor='rgba(148, 163, 184, 0.45)',
            showland=True,
            landcolor='rgba(148, 163, 184, 0.18)',
            lakecolor='rgba(0,0,0,0)',
            projection_type='natural earth',
            resolution=50,
            lataxis_range=[34, 60.5],
            lonaxis_range=[-11, 46],
        ),
        margin=dict(l=10, r=10, t=50, b=10),
        height=500,
    )
    return fig


def render(df: pd.DataFrame):
    st.plotly_chart(build(df), width="stretch")
