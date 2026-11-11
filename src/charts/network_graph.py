"""
5. ADVANCED: Network Graph (Takımlar Arası Üstünlük Ağı)
Insight: Directed dominance network among top teams in the selected league.
"""

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.theme import THEME_TEMPLATE


def build(df: pd.DataFrame, selected_league: str = 'Premier League', top_n: int = 8) -> go.Figure:
    sub_df = df[df['league_name'] == selected_league]
    if sub_df.empty:
        sub_df = df

    # Find top N teams by total wins
    top_teams = sub_df[sub_df['ftr'] == 'H']['home_team'].value_counts().head(top_n).index.tolist()
    filtered = sub_df[(sub_df['home_team'].isin(top_teams)) & (sub_df['away_team'].isin(top_teams))]

    G = nx.DiGraph()
    for team in top_teams:
        G.add_node(team)

    for _, row in filtered.iterrows():
        if row['ftr'] == 'H':
            winner, loser = row['home_team'], row['away_team']
        elif row['ftr'] == 'A':
            winner, loser = row['away_team'], row['home_team']
        else:
            continue
        if G.has_edge(winner, loser):
            G[winner][loser]['weight'] += 1
        else:
            G.add_edge(winner, loser, weight=1)

    pos = nx.circular_layout(G)

    # Edge traces
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1.2, color='rgba(148, 163, 184, 0.4)'),
        hoverinfo='none',
        mode='lines'
    )

    # Node traces
    node_x, node_y, node_text, node_size = [], [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        out_deg = G.out_degree(node, weight='weight')
        in_deg = G.in_degree(node, weight='weight')
        node_text.append(f"<b>{node}</b><br>Wins: {out_deg}<br>Losses: {in_deg}")
        node_size.append(20 + out_deg * 3)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=[n for n in G.nodes()],
        textposition="top center",
        hovertext=node_text,
        marker=dict(
            showscale=True,
            colorscale='YlGnBu',
            size=node_size,
            color=[G.out_degree(n, weight='weight') for n in G.nodes()],
            colorbar=dict(thickness=12, title="Total Wins", xanchor="left"),
            line=dict(width=2, color='#FFFFFF')
        )
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title=f"🕸️ 5. Head-to-Head Dominance Network ({selected_league} Top Teams)",
        template=THEME_TEMPLATE,
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=50),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=480
    )
    return fig


def render(df: pd.DataFrame):
    league = st.selectbox(
        "Select League for Network Dominance Analysis:",
        options=sorted(df['league_name'].unique()),
        key="network_graph_league",
    )
    st.plotly_chart(build(df, selected_league=league), width="stretch")
