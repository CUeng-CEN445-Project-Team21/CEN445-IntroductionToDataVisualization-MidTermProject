"""
sidebar.py - Filter panel. render() draws the widgets and returns the filtered dataframe.

To add a filter: add a widget in render() with a key from FILTER_KEYS, pass its value to
apply_filters(), filter there.
"""

import math

import pandas as pd
import streamlit as st

ALL_SEASONS = "All"

# Every filter widget's key. "Reset filters" deletes these so each widget falls back to its default.
FILTER_KEYS = ["filter_leagues", "filter_season", "filter_goals", "filter_home_odds", "filter_comebacks"]


def apply_filters(df: pd.DataFrame, leagues, season, goal_range, max_home_odds, comebacks_only) -> pd.DataFrame:
    out = df
    if leagues:                       # nothing selected = all leagues
        out = out[out['league_name'].isin(leagues)]
    if season and season != ALL_SEASONS:
        out = out[out['season'] == season]
    out = out[
        out['total_goals'].between(goal_range[0], goal_range[1]) &
        (out['home_odds'] <= max_home_odds)
    ]
    if comebacks_only:
        out = out[
            ((out['htr'] == 'A') & (out['ftr'] == 'H')) |
            ((out['htr'] == 'H') & (out['ftr'] == 'A'))
        ]
    return out


def _reset_filters():
    for key in FILTER_KEYS:
        st.session_state.pop(key, None)


def _season_label(season: str) -> str:
    """'2024-2025' -> '24/25' so the season buttons fit in the sidebar."""
    if season == ALL_SEASONS:
        return "All seasons"
    start, _, end = season.partition("-")
    return f"{start[-2:]}/{end[-2:]}" if end else season


def render(df_raw: pd.DataFrame) -> pd.DataFrame:
    with st.sidebar:
        st.markdown("## Filters")
        st.caption("Every chart and model on the page uses these filters.")

        # --- Competition ------------------------------------------------------
        st.markdown('<div class="side-label">Competition</div>', unsafe_allow_html=True)
        leagues = st.multiselect(
            "Leagues",
            options=sorted(df_raw['league_name'].unique().tolist()),
            default=[],
            placeholder="All leagues",
            key="filter_leagues",
        )

        seasons = [ALL_SEASONS] + sorted(df_raw['season'].unique().tolist(), reverse=True)
        season = st.segmented_control(
            "Season",
            options=seasons,
            default=ALL_SEASONS,
            format_func=_season_label,
            key="filter_season",
            width="stretch",
        )

        # --- Match profile ----------------------------------------------------
        st.markdown('<div class="side-label">Match profile</div>', unsafe_allow_html=True)
        min_goals, max_goals = int(df_raw['total_goals'].min()), int(df_raw['total_goals'].max())
        goal_range = st.slider(
            "Total goals in match",
            min_value=min_goals,
            max_value=max_goals,
            value=(min_goals, max_goals),
            key="filter_goals",
        )

        # Upper bound follows the data so nothing is hidden by default
        odds_ceiling = float(math.ceil(df_raw['home_odds'].max()))
        max_home_odds = st.slider(
            "Max home win odds",
            min_value=1.0,
            max_value=odds_ceiling,
            value=odds_ceiling,
            step=0.5,
            format="%.1f",
            help="Lower it to keep only matches where the home side was a clear favourite.",
            key="filter_home_odds",
        )

        comebacks_only = st.toggle(
            "Comebacks only",
            help="Matches where the team losing at half-time won at full-time.",
            key="filter_comebacks",
        )

        filtered = apply_filters(df_raw, leagues, season, goal_range, max_home_odds, comebacks_only)

        # --- Summary ----------------------------------------------------------
        st.divider()
        share = len(filtered) / len(df_raw) if len(df_raw) else 0
        st.markdown(f"**{len(filtered):,}** of {len(df_raw):,} matches")
        st.progress(share)
        st.button("Reset filters", icon=":material/restart_alt:", on_click=_reset_filters, width="stretch")
        st.caption(f"Dataset: {df_raw['league_name'].nunique()} leagues · "
                   f"{df_raw['season'].nunique()} seasons · {df_raw.shape[1]} columns")

    return filtered
