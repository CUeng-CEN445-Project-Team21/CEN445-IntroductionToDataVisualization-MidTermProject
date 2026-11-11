"""
schema.py - The data contract shared by the pipeline and every chart.

If you add a column to the dataset, add it here so the rest of the team knows it exists.
"""

# ------------------------------------------------------------------------------
# Leagues the pipeline knows about (football-data.co.uk division codes).
# Matches from a division that is not listed here are skipped with a warning,
# so to add a league, add one line.
#
# Note: the choropleth map draws one league per country. Adding a second league
# from the same country (e.g. E1 Championship) will overlap on the map.
# ------------------------------------------------------------------------------
LEAGUE_METADATA = {
    'E0':  {'league': 'Premier League', 'country': 'England',     'iso3': 'GBR'},
    'F1':  {'league': 'Ligue 1',        'country': 'France',      'iso3': 'FRA'},
    'D1':  {'league': 'Bundesliga',     'country': 'Germany',     'iso3': 'DEU'},
    'I1':  {'league': 'Serie A',        'country': 'Italy',       'iso3': 'ITA'},
    'N1':  {'league': 'Eredivisie',     'country': 'Netherlands', 'iso3': 'NLD'},
    'P1':  {'league': 'Primeira Liga',  'country': 'Portugal',    'iso3': 'PRT'},
    'T1':  {'league': 'Süper Lig',      'country': 'Turkey',      'iso3': 'TUR'},
    'SP1': {'league': 'La Liga',        'country': 'Spain',       'iso3': 'ESP'},
    'B1':  {'league': 'Pro League',     'country': 'Belgium',     'iso3': 'BEL'},
    'G1':  {'league': 'Super League',   'country': 'Greece',      'iso3': 'GRC'},
}

# ------------------------------------------------------------------------------
# Base columns: what every input file is converted to before enrichment.
# Required ones must be present and valid, otherwise the row is dropped.
# ------------------------------------------------------------------------------
REQUIRED_COLUMNS = [
    'division', 'season', 'match_date', 'home_team', 'away_team',
    'fthg', 'ftag', 'ftr',          # full-time home goals, away goals, result (H/D/A)
    'hthg', 'htag', 'htr',          # half-time home goals, away goals, result (H/D/A)
    'home_odds', 'draw_odds', 'away_odds',
]
OPTIONAL_COLUMNS = ['id', 'over_25_odds', 'under_25_odds']
BASE_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

# Columns that uniquely identify a match (used to drop duplicates across files).
MATCH_KEY = ['division', 'match_date', 'home_team', 'away_team']

# ------------------------------------------------------------------------------
# Final column order of data/processed/matches.parquet  (what charts receive)
#
#   id                 int    unique match id
#   division           str    football-data code, e.g. 'E0'
#   league_name        str    'Premier League'
#   country / country_iso3    'England' / 'GBR'
#   season             str    '2024-2025'
#   match_date         str    'YYYY-MM-DD'
#   home_team / away_team
#   fthg / ftag / ftr  full-time goals and result ('H', 'D', 'A')
#   hthg / htag / htr  half-time goals and result
#   result_label / ht_result_label   'Home Win' / 'Draw' / 'Away Win'
#   total_goals, goal_diff (home - away)
#   is_over_25, btts   0/1 flags
#   match_flow         HT -> FT story, e.g. 'Home Comeback (Lost HT -> Won FT)'
#   home_odds / draw_odds / away_odds / over_25_odds / under_25_odds
#   prob_home / prob_draw / prob_away   bookmaker-margin-free probabilities
# ------------------------------------------------------------------------------
OUTPUT_COLUMNS = [
    'id', 'division', 'league_name', 'country', 'country_iso3', 'season', 'match_date',
    'home_team', 'away_team', 'fthg', 'ftag', 'ftr', 'result_label',
    'hthg', 'htag', 'htr', 'ht_result_label',
    'total_goals', 'goal_diff', 'is_over_25', 'btts', 'match_flow',
    'home_odds', 'draw_odds', 'away_odds', 'over_25_odds', 'under_25_odds',
    'prob_home', 'prob_draw', 'prob_away',
]
