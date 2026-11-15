"""
4. ADVANCED: Parallel Coordinates (Takımların İstatistik Profili)
Question: What does each team's full statistical profile look like?

One line = one team. Seven axes, left to right: points per game, goals scored / match,
goals conceded / match, win %, draw %, clean-sheet %, BTTS %. Line colour = points per game.

Team stats come from a long table with one row per team per match (home side: goals for =
fthg, against = ftag; away side the reverse). Plotly parcoords has no hover, so drag on any
axis to keep only the teams inside that range; the table below names the teams.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.theme import THEME_TEMPLATE

ALL_LEAGUES = "All leagues"
MIN_MATCHES = 15   # same cut-off as ML1; every team has 15+ matches under the default filters

# (column, axis label, tick format)
AXES = [
    ('ppg',             'Points / game',          '.2f'),
    ('scored_pm',       'Goals scored / match',   '.2f'),
    ('conceded_pm',     'Goals conceded / match', '.2f'),
    ('win_pct',         'Win %',                  '.0f'),
    ('draw_pct',        'Draw %',                 '.0f'),
    ('clean_sheet_pct', 'Clean-sheet %',          '.0f'),
    ('btts_pct',        'BTTS %',                 '.0f'),
]

# Single-hue blue ramp, light -> dark = low -> high points per game. The ends stay off the
# extremes so the lines read on both Streamlit's light and dark backgrounds.
PPG_COLORSCALE = [[0, '#b7d3f6'], [0.5, '#3987e5'], [1, '#104281']]


def team_long(df: pd.DataFrame) -> pd.DataFrame:
    """One row per team per match, from that team's point of view."""
    home = pd.DataFrame({
        'team': df['home_team'], 'league_name': df['league_name'],
        'gf': df['fthg'], 'ga': df['ftag'], 'btts': df['btts'],
        'win': df['ftr'] == 'H', 'draw': df['ftr'] == 'D',
    })
    away = pd.DataFrame({
        'team': df['away_team'], 'league_name': df['league_name'],
        'gf': df['ftag'], 'ga': df['fthg'], 'btts': df['btts'],
        'win': df['ftr'] == 'A', 'draw': df['ftr'] == 'D',
    })
    return pd.concat([home, away], ignore_index=True)


def team_profiles(df: pd.DataFrame) -> pd.DataFrame:
    """The seven profile stats for every team with at least MIN_MATCHES matches."""
    long = team_long(df)
    t = long.groupby('team').agg(
        league_name=('league_name', lambda s: s.mode().iat[0]),
        matches=('gf', 'size'),
        wins=('win', 'sum'), draws=('draw', 'sum'),
        goals_for=('gf', 'sum'), goals_against=('ga', 'sum'),
        clean_sheets=('ga', lambda s: (s == 0).sum()),
        btts=('btts', 'sum'),
    )
    t = t[t['matches'] >= MIN_MATCHES]
    m = t['matches']
    t['ppg'] = (3 * t['wins'] + t['draws']) / m
    t['scored_pm'] = t['goals_for'] / m
    t['conceded_pm'] = t['goals_against'] / m
    t['win_pct'] = t['wins'] / m * 100
    t['draw_pct'] = t['draws'] / m * 100
    t['clean_sheet_pct'] = t['clean_sheets'] / m * 100
    t['btts_pct'] = t['btts'] / m * 100
    return t.sort_values('ppg', ascending=False)


def build(df: pd.DataFrame, league: str = ALL_LEAGUES) -> tuple[go.Figure, pd.DataFrame]:
    if league != ALL_LEAGUES:
        df = df[df['league_name'] == league]
    teams = team_profiles(df)
    if teams.empty:
        raise ValueError(f"No team has {MIN_MATCHES}+ matches in the current filter. "
                         "Broaden the sidebar filters to see team profiles.")

    fig = go.Figure(go.Parcoords(
        line=dict(
            color=teams['ppg'], colorscale=PPG_COLORSCALE, showscale=True,
            colorbar=dict(title=dict(text="Points<br>/ game"), thickness=12, len=0.8),
        ),
        dimensions=[dict(label=label, values=teams[col], tickformat=fmt) for col, label, fmt in AXES],
        labelangle=0,
        labelside='top',
    ))
    where = "all leagues" if league == ALL_LEAGUES else league
    fig.update_layout(
        title=dict(text=f"📈 4. Team profiles · {len(teams)} teams · {where}", x=0, xanchor='left'),
        template=THEME_TEMPLATE,
        height=480,
        margin=dict(l=60, r=90, t=100, b=30),
    )
    return fig, teams


def _table(teams: pd.DataFrame):
    cols = {'league_name': 'League', 'matches': 'Matches'} | {c: label for c, label, _ in AXES}
    table = teams[list(cols)].rename(columns=cols)
    st.dataframe(
        table, width="stretch",
        column_config={label: st.column_config.NumberColumn(format="%.2f" if fmt == '.2f' else "%.0f%%")
                       for _, label, fmt in AXES},
    )


def render(df: pd.DataFrame):
    leagues = sorted(df['league_name'].unique())
    league = st.selectbox("League", [ALL_LEAGUES] + leagues, key="parallel_coordinates_league")
    try:
        fig, teams = build(df, league)
    except ValueError as e:
        st.info(str(e))
        return

    st.plotly_chart(fig, width="stretch", config={'displaylogo': False})
    st.caption(
        "One line per team, darker blue = more points per game. **Drag along any axis** to keep only "
        "the teams in that range (drag several axes to combine; click the axis outside the range to clear). "
        f"Teams with fewer than {MIN_MATCHES} matches in the current filter are left out."
    )
    with st.expander(f"🔍 Team table ({len(teams)} teams, sorted by points per game)"):
        _table(teams)
