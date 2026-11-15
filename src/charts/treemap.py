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
    # Team level goals and matches played
    home_g = df.groupby(['league_name', 'home_team']).agg(
        goals=('fthg', 'sum'), matches=('id', 'count')
    ).reset_index().rename(columns={'home_team': 'team'})
    away_g = df.groupby(['league_name', 'away_team']).agg(
        goals=('ftag', 'sum'), matches=('id', 'count')
    ).reset_index().rename(columns={'away_team': 'team'})

    team_stats = pd.concat([home_g, away_g]).groupby(['league_name', 'team'], as_index=False)[['goals', 'matches']].sum()

    # Wins calculation
    home_w = df[df['ftr'] == 'H'].groupby(['league_name', 'home_team']).size().reset_index(name='wins')
    home_w.columns = ['league_name', 'team', 'wins']
    away_w = df[df['ftr'] == 'A'].groupby(['league_name', 'away_team']).size().reset_index(name='wins')
    away_w.columns = ['league_name', 'team', 'wins']
    team_wins = pd.concat([home_w, away_w]).groupby(['league_name', 'team'], as_index=False)['wins'].sum()

    merged = pd.merge(team_stats, team_wins, on=['league_name', 'team'], how='left').fillna(0)
    merged['goals'] = merged['goals'].astype(int)
    merged['matches'] = merged['matches'].astype(int)
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

    # Build clean per-node hover summary keyed by full treemap node id
    team_lookup = merged.set_index(['league_name', 'team'])[['matches', 'wins']].to_dict('index')
    league_matches = df.groupby('league_name')['id'].count().to_dict()
    total_matches = len(df)
    trace = fig.data[0]
    node_notes = []
    for node_id, label, color_val in zip(trace.ids, trace.labels, trace.marker.colors):
        parts = node_id.split('/')
        if len(parts) == 1:
            node_notes.append(f"Total Matches: <b>{total_matches:,}</b>")
        elif len(parts) == 2:
            m_cnt = league_matches.get(label, 0)
            node_notes.append(f"League Matches: <b>{m_cnt:,}</b><br>Avg Team Wins: <b>{color_val:.1f}</b>")
        else:
            league_name, team_name = parts[1], parts[2]
            info = team_lookup.get((league_name, team_name), {'matches': 0, 'wins': 0})
            m_cnt, w_cnt = info['matches'], info['wins']
            win_pct = (w_cnt / m_cnt * 100) if m_cnt else 0.0
            node_notes.append(
                f"Matches: <b>{m_cnt:,}</b><br>Wins: <b>{w_cnt:,}</b> (<b>{win_pct:.1f}%</b>)"
            )

    fig.update_traces(
        textinfo="label+value",
        tiling=dict(packing='squarify'),
        marker=dict(line=dict(width=1, color='rgba(148, 163, 184, 0.5)')),
        customdata=node_notes,
        hovertemplate=(
            "<b>%{label}</b><br><br>"
            "Total Goals: <b>%{value:,}</b><br>"
            "%{customdata}<br>"
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
    n_teams = pd.concat([df['home_team'], df['away_team']]).nunique()
    st.caption(
        f"Area = goals scored, colour = wins ({n_teams} clubs across {len(df):,} matches; "
        "promoted/relegated clubs appear in 1 season). Click a league to zoom."
    )
