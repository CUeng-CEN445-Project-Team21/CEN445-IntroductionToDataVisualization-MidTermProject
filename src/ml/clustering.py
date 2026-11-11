"""
ML 1. K-MEANS CLUSTERING: Team Tactical Profiles
Groups teams by goals scored, goals conceded and win rate.
"""

import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from src.theme import THEME_TEMPLATE

MIN_MATCHES = 15  # teams with fewer matches in the current filter are left out


def run_team_clustering(df: pd.DataFrame, n_clusters: int = 3):
    """
    Computes per-team statistics across matches and clusters them using K-Means.
    Returns: (team_df, scatter_plot_figure). Raises ValueError if there are too few teams.
    """
    # 1. Aggregate Team Statistics
    home_stats = df.groupby('home_team').agg(
        matches=('id', 'count'),
        goals_for=('fthg', 'sum'),
        goals_against=('ftag', 'sum'),
        wins=('ftr', lambda x: (x == 'H').sum())
    )

    away_stats = df.groupby('away_team').agg(
        matches=('id', 'count'),
        goals_for=('ftag', 'sum'),
        goals_against=('fthg', 'sum'),
        wins=('ftr', lambda x: (x == 'A').sum())
    )

    teams = home_stats.add(away_stats, fill_value=0)
    teams = teams[teams['matches'] >= MIN_MATCHES]
    if len(teams) < n_clusters:
        raise ValueError(
            f"Only {len(teams)} teams have {MIN_MATCHES}+ matches in the current filter, "
            f"which is not enough for {n_clusters} clusters. Broaden the sidebar filters."
        )

    teams['goals_per_match'] = (teams['goals_for'] / teams['matches']).round(2)
    teams['conceded_per_match'] = (teams['goals_against'] / teams['matches']).round(2)
    teams['win_rate'] = (teams['wins'] / teams['matches'] * 100).round(1)
    teams['goal_diff_per_match'] = (teams['goals_per_match'] - teams['conceded_per_match']).round(2)

    features = ['goals_per_match', 'conceded_per_match', 'win_rate']
    X = teams[features]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    teams['cluster'] = kmeans.fit_predict(X_scaled)

    # Meaningful cluster labels sorted by win rate
    cluster_order = teams.groupby('cluster')['win_rate'].mean().sort_values(ascending=False).index
    if n_clusters == 3:
        names = ["Elite Dominators", "Balanced Competitors", "Relegation Strugglers"]
    else:
        names = [f"Tier {i + 1} Teams" for i in range(n_clusters)]
    label_map = dict(zip(cluster_order, names))

    teams['cluster_label'] = teams['cluster'].map(label_map)
    teams['team_name'] = teams.index

    # Visualization: Goals Scored vs Conceded colored by Cluster
    fig = px.scatter(
        teams.reset_index(),
        x='goals_per_match',
        y='conceded_per_match',
        color='cluster_label',
        size='win_rate',
        hover_name='team_name',
        hover_data={'goals_per_match': ':.2f', 'conceded_per_match': ':.2f', 'win_rate': ':.1f%'},
        labels={
            'goals_per_match': 'Avg Goals Scored / Match',
            'conceded_per_match': 'Avg Goals Conceded / Match',
            'cluster_label': 'Team Profile Tier'
        },
        color_discrete_map={
            "Elite Dominators": "#10B981",       # Emerald
            "Balanced Competitors": "#3B82F6",   # Blue
            "Relegation Strugglers": "#EF4444"   # Red
        },
        category_orders={'cluster_label': names},
        title=f"🤖 ML 1: Team Tactical Clustering (K-Means, k={n_clusters})"
    )

    fig.update_layout(
        template=THEME_TEMPLATE,
        yaxis=dict(autorange="reversed"),  # Top is lower conceded (better defense)
        height=480,
        margin=dict(l=10, r=10, t=50, b=10)
    )

    return teams, fig


def render(df: pd.DataFrame):
    st.markdown("#### 1️⃣ K-Means Clustering: Team Tactical Archetypes")
    n_clusters = st.slider("Select Number of Clusters (k):", min_value=2, max_value=5, value=3,
                           key="clustering_k")
    try:
        teams_df, cluster_fig = run_team_clustering(df, n_clusters=n_clusters)
    except ValueError as e:
        st.info(str(e))
        return

    st.plotly_chart(cluster_fig, width="stretch")
    with st.expander("🔍 View Clustered Team Profiles Table"):
        st.dataframe(
            teams_df[['team_name', 'cluster_label', 'matches', 'goals_per_match', 'conceded_per_match', 'win_rate']],
            width="stretch"
        )
