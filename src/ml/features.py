"""
features.py - Pre-match team-strength features for the classifier (ML 2). Not drawn itself.

Every number is what was known *before* kick-off: matches are replayed in date order and a
match only ever sees the results that came before it. Features are built from the full
dataset, not the filtered one, so a sidebar filter can't cut a team's history short.

Per match (index = match id):
  elo_home / elo_away         Elo rating going into the match
  form_pts_home / _away       points per game over the team's previous FORM_N matches
  form_gd_home / _away        goal difference per game over the previous FORM_N matches
  prior_home / prior_away     how many earlier matches the team has in the dataset
  elo_diff, form_pts_diff, form_gd_diff   home minus away

Per team (team_state): the same ratings *after* its last match, for the simulator.

Elo: every team starts at ELO_START in August 2023. After each match both ratings move by
ELO_K x (result - expected result), scaled up for bigger winning margins. The home side gets
ELO_HOME extra points when the expected result is worked out.
"""

import numpy as np
import pandas as pd
import streamlit as st

ELO_START = 1500
ELO_K = 20
ELO_HOME = 60
FORM_N = 5
WARMUP = FORM_N   # matches where either team has fewer earlier matches than this are left out


def _team_long(df: pd.DataFrame) -> pd.DataFrame:
    """One row per team per match, in date order, from that team's point of view."""
    home = pd.DataFrame({'id': df['id'], 'date': df['match_date'], 'team': df['home_team'],
                         'league_name': df['league_name'], 'side': 'home',
                         'pts': df['ftr'].map({'H': 3, 'D': 1, 'A': 0}), 'gd': df['fthg'] - df['ftag']})
    away = pd.DataFrame({'id': df['id'], 'date': df['match_date'], 'team': df['away_team'],
                         'league_name': df['league_name'], 'side': 'away',
                         'pts': df['ftr'].map({'H': 0, 'D': 1, 'A': 3}), 'gd': df['ftag'] - df['fthg']})
    long = pd.concat([home, away], ignore_index=True)
    return long.sort_values(['date', 'id'], kind='stable').reset_index(drop=True)


def _elo(df: pd.DataFrame):
    """Elo before every match (two arrays, in df order) and every team's rating after its last match."""
    ratings, before_home, before_away = {}, [], []
    score = {'H': 1.0, 'D': 0.5, 'A': 0.0}
    for home, away, fthg, ftag, ftr in df[['home_team', 'away_team', 'fthg', 'ftag', 'ftr']].itertuples(index=False):
        h, a = ratings.get(home, ELO_START), ratings.get(away, ELO_START)
        before_home.append(h)
        before_away.append(a)
        expected = 1.0 / (1.0 + 10 ** ((a - (h + ELO_HOME)) / 400))
        margin = abs(fthg - ftag)
        change = ELO_K * (np.log(margin + 1) + 1 if margin else 1.0) * (score[ftr] - expected)
        ratings[home], ratings[away] = h + change, a - change
    return np.array(before_home), np.array(before_away), ratings


@st.cache_data(show_spinner=False)
def match_features(full: pd.DataFrame) -> pd.DataFrame:
    df = full.sort_values(['match_date', 'id'], kind='stable').reset_index(drop=True)

    long = _team_long(df)
    by_team = long.groupby('team')
    # shift(1): a match's own result never feeds its own features
    long['form_pts'] = by_team['pts'].transform(lambda s: s.shift(1).rolling(FORM_N, min_periods=1).mean())
    long['form_gd'] = by_team['gd'].transform(lambda s: s.shift(1).rolling(FORM_N, min_periods=1).mean())
    long['prior'] = by_team.cumcount()

    cols = ['form_pts', 'form_gd', 'prior']
    home = long[long['side'] == 'home'].set_index('id')[cols].add_suffix('_home')
    away = long[long['side'] == 'away'].set_index('id')[cols].add_suffix('_away')

    elo_home, elo_away, _ = _elo(df)
    out = pd.DataFrame({'elo_home': elo_home, 'elo_away': elo_away}, index=df['id'])
    out = out.join(home).join(away)
    out['elo_diff'] = out['elo_home'] - out['elo_away']
    out['form_pts_diff'] = out['form_pts_home'] - out['form_pts_away']
    out['form_gd_diff'] = out['form_gd_home'] - out['form_gd_away']
    return out


@st.cache_data(show_spinner=False)
def team_state(full: pd.DataFrame) -> pd.DataFrame:
    """Each team's Elo and last-FORM_N form after its most recent match in the dataset."""
    df = full.sort_values(['match_date', 'id'], kind='stable').reset_index(drop=True)
    long = _team_long(df)
    last = long.groupby('team').tail(FORM_N).groupby('team')
    state = pd.DataFrame({
        'league_name': long.groupby('team')['league_name'].last(),
        'last_match': long.groupby('team')['date'].last(),
        'form_pts': last['pts'].mean(),
        'form_gd': last['gd'].mean(),
    })
    _, _, ratings = _elo(df)
    state['elo'] = pd.Series(ratings)
    return state
