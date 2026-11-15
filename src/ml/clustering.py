"""
ML 1. K-MEANS CLUSTERING: Team Archetypes
Question: do teams fall into natural tiers by how they score, concede and win?

Every team with MIN_MATCHES+ matches in the filter is described by three numbers: goals scored
per match, goals conceded per match and win %. Each number is scaled to mean 0 / sd 1 first
(otherwise win %, on a 0-100 scale, would drown out the goal rates), then K-Means groups the
teams into k tiers. Tiers are ranked by average win % and named best -> worst.

"Rate teams within their own league" scales each league separately, so a team is compared
with its own league only: the best side of a weaker league can then reach the top tier too.

The silhouette chart scores how cleanly the teams separate for each k (-1..1, higher =
cleaner). It drops after k = 4, which is why the slider stops there; four is also the most
tiers the colour ramp can keep apart.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from src.theme import THEME_TEMPLATE

MIN_MATCHES = 15        # teams with fewer matches in the current filter are left out
K_CHOICES = (2, 3, 4)
K_DIAGNOSTIC = range(2, 7)
FEATURES = ['goals_per_match', 'conceded_per_match', 'win_rate']

TIER_NAMES = {
    2: ["Upper Tier", "Lower Tier"],
    3: ["Elite Dominators", "Balanced Competitors", "Relegation Strugglers"],
    4: ["Elite Dominators", "Contenders", "Mid-table", "Relegation Strugglers"],
}
# Ordinal blue ramp, best tier darkest. Each set is checked (one hue, visible steps, ends
# readable on both light and dark backgrounds).
TIER_COLORS = {
    2: ['#256abf', '#86b6ef'],
    3: ['#184f95', '#2a78d6', '#86b6ef'],
    4: ['#184f95', '#2a78d6', '#5598e7', '#86b6ef'],
}
TIER_SYMBOLS = ['circle', 'diamond', 'square', 'triangle-up']   # second cue, so tiers aren't colour-only
HIGHLIGHT = '#2a78d6'
MUTED = '#898781'


def team_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Per-team totals and rates for every team with MIN_MATCHES+ matches."""
    home = pd.DataFrame({'team': df['home_team'], 'league_name': df['league_name'],
                         'gf': df['fthg'], 'ga': df['ftag'], 'win': df['ftr'] == 'H'})
    away = pd.DataFrame({'team': df['away_team'], 'league_name': df['league_name'],
                         'gf': df['ftag'], 'ga': df['fthg'], 'win': df['ftr'] == 'A'})
    teams = pd.concat([home, away]).groupby('team').agg(
        league_name=('league_name', lambda s: s.mode().iat[0]),
        matches=('gf', 'size'), goals_for=('gf', 'sum'), goals_against=('ga', 'sum'), wins=('win', 'sum'),
    )
    teams = teams[teams['matches'] >= MIN_MATCHES].copy()
    teams['goals_per_match'] = teams['goals_for'] / teams['matches']
    teams['conceded_per_match'] = teams['goals_against'] / teams['matches']
    teams['win_rate'] = teams['wins'] / teams['matches'] * 100
    return teams


def _scaled(teams: pd.DataFrame, within_league: bool) -> np.ndarray:
    X = teams[FEATURES]
    if within_league:
        X = X.groupby(teams['league_name']).transform(lambda s: (s - s.mean()) / s.std(ddof=0)).fillna(0)
    return StandardScaler().fit_transform(X)


@st.cache_data(show_spinner=False)
def run_team_clustering(df: pd.DataFrame, n_clusters: int = 3, within_league: bool = False):
    """
    Returns (teams, silhouette): teams gets 'tier' (0 = best) and 'cluster_label';
    silhouette maps every k in K_DIAGNOSTIC to its score. Raises ValueError if there are too few teams.
    """
    teams = team_stats(df)
    if len(teams) <= n_clusters + 1:
        raise ValueError(
            f"Only {len(teams)} teams have {MIN_MATCHES}+ matches in the current filter, which is not "
            f"enough for {n_clusters} tiers. Broaden the sidebar filters."
        )
    X = _scaled(teams, within_league)

    silhouette, labels = {}, None
    for k in (k for k in K_DIAGNOSTIC if k < len(teams) - 1):   # silhouette needs k < number of teams
        fitted = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(X)
        silhouette[k] = float(silhouette_score(X, fitted))
        if k == n_clusters:
            labels = fitted

    # Rank clusters by average win % so tier 0 is always the best
    order = teams.groupby(labels)['win_rate'].mean().sort_values(ascending=False).index
    rank = {cluster: i for i, cluster in enumerate(order)}
    teams['tier'] = [rank[c] for c in labels]
    teams['cluster_label'] = teams['tier'].map(dict(enumerate(TIER_NAMES[n_clusters])))
    teams['team_name'] = teams.index
    return teams, silhouette


# ── Figures ──────────────────────────────────────────────────────────────────────────────────

def scatter_figure(teams: pd.DataFrame, k: int) -> go.Figure:
    fig = go.Figure()
    centres = teams.groupby('tier')[['goals_per_match', 'conceded_per_match']].mean()
    for tier, name in enumerate(TIER_NAMES[k]):
        t = teams[teams['tier'] == tier]
        fig.add_scatter(
            x=t['goals_per_match'], y=t['conceded_per_match'], mode='markers', name=f"{name} ({len(t)})",
            marker=dict(color=TIER_COLORS[k][tier], symbol=TIER_SYMBOLS[tier], size=10, opacity=0.9,
                        line=dict(width=1, color='rgba(255,255,255,0.65)')),
            customdata=np.column_stack([t['league_name'], t['matches'], t['win_rate']]),
            text=t.index,
            hovertemplate="<b>%{text}</b> · %{customdata[0]}<br>"
                          f"Tier: {name}<br>"
                          "Scored %{x:.2f} / match · conceded %{y:.2f} / match<br>"
                          "Win rate %{customdata[2]:.1f}% · %{customdata[1]} matches<extra></extra>",
        )
        # Direct label at the tier's centre, so identity never depends on colour alone
        fig.add_annotation(x=centres.at[tier, 'goals_per_match'], y=centres.at[tier, 'conceded_per_match'],
                           text=f"<b>{name}</b>", showarrow=False, yshift=-16, font_size=12, opacity=0.9)
        fig.add_scatter(x=[centres.at[tier, 'goals_per_match']], y=[centres.at[tier, 'conceded_per_match']],
                        mode='markers', showlegend=False, hoverinfo='skip',
                        marker=dict(symbol='x-thin', size=16, line=dict(width=2.5, color=TIER_COLORS[k][tier])))
    fig.update_layout(
        template=THEME_TEMPLATE, height=480,
        title=dict(text=f"Teams by goals scored and conceded · k = {k}", font_size=15),
        xaxis=dict(title="Goals scored per match →", zeroline=False),
        yaxis=dict(title="Goals conceded per match (better defence ↑)", autorange='reversed', zeroline=False),
        legend=dict(orientation='h', yanchor='bottom', y=1.0, xanchor='left', x=0, title_text=""),
        margin=dict(l=10, r=10, t=80, b=10),
    )
    return fig


def silhouette_figure(silhouette: dict, k: int) -> go.Figure:
    ks = list(silhouette)
    values = [silhouette[i] for i in ks]
    fig = go.Figure(go.Bar(
        x=[f"k={i}" for i in ks], y=values,
        marker_color=[HIGHLIGHT if i == k else MUTED for i in ks],
        text=[f"{v:.2f}" for v in values], textposition='outside', cliponaxis=False,
        hovertemplate="%{x}: silhouette %{y:.3f}<extra></extra>",
    ))
    fig.update_layout(
        template=THEME_TEMPLATE, height=480, bargap=0.35,
        title=dict(text="How cleanly the tiers separate", font_size=15),
        yaxis=dict(title="Silhouette score (higher = cleaner)", range=[0, max(values) * 1.2], tickformat='.1f'),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


# ── Page ─────────────────────────────────────────────────────────────────────────────────────

def render(df: pd.DataFrame):
    st.markdown("#### 1️⃣ K-Means Clustering: Team Tactical Archetypes")
    st.caption("Do teams fall into natural tiers by how much they score, concede and win? "
               f"Each dot is a team with {MIN_MATCHES}+ matches in the current filter.")

    c_k, c_within = st.columns([2, 1], vertical_alignment="bottom")
    with c_k:
        k = st.select_slider("Number of tiers (k)", options=K_CHOICES, value=3, key="clustering_k")
    with c_within:
        within = st.toggle("Rate teams within their own league", key="clustering_within",
                           help="Compare each team only with its own league, so league strength "
                                "doesn't decide the tier.")
    try:
        teams, silhouette = run_team_clustering(df, n_clusters=k, within_league=within)
    except ValueError as e:
        st.info(str(e))
        return

    col_scatter, col_sil = st.columns([2, 1])
    with col_scatter:
        st.plotly_chart(scatter_figure(teams, k), width="stretch", config={'displaylogo': False})
    with col_sil:
        st.plotly_chart(silhouette_figure(silhouette, k), width="stretch", config={'displaylogo': False})
        best = max(silhouette, key=silhouette.get)
        st.caption(f"k = {best} separates most cleanly in the current filter. On the full dataset the "
                   "score falls past k = 4, so the slider stops there; 5 and 6 are shown for comparison only.")

    profile = teams.groupby('cluster_label', sort=False).agg(
        teams=('matches', 'size'), goals_per_match=('goals_per_match', 'mean'),
        conceded_per_match=('conceded_per_match', 'mean'), win_rate=('win_rate', 'mean'),
        example=('win_rate', lambda s: s.idxmax()),
    ).reindex(TIER_NAMES[k])
    st.dataframe(
        profile.reset_index().rename(columns={
            'cluster_label': 'Tier', 'teams': 'Teams', 'goals_per_match': 'Scored / match',
            'conceded_per_match': 'Conceded / match', 'win_rate': 'Win %', 'example': 'Best team in tier'}),
        hide_index=True, width="stretch",
        column_config={'Scored / match': st.column_config.NumberColumn(format="%.2f"),
                       'Conceded / match': st.column_config.NumberColumn(format="%.2f"),
                       'Win %': st.column_config.NumberColumn(format="%.1f%%")},
    )
    with st.expander("🔍 Every team and its tier"):
        st.dataframe(
            teams.sort_values(['tier', 'win_rate'], ascending=[True, False])[
                ['team_name', 'league_name', 'cluster_label', 'matches', 'goals_per_match',
                 'conceded_per_match', 'win_rate']].rename(columns={
                    'team_name': 'Team', 'league_name': 'League', 'cluster_label': 'Tier', 'matches': 'Matches',
                    'goals_per_match': 'Scored / match', 'conceded_per_match': 'Conceded / match',
                    'win_rate': 'Win %'}),
            hide_index=True, width="stretch",
            column_config={'Scored / match': st.column_config.NumberColumn(format="%.2f"),
                           'Conceded / match': st.column_config.NumberColumn(format="%.2f"),
                           'Win %': st.column_config.NumberColumn(format="%.1f%%")},
        )
