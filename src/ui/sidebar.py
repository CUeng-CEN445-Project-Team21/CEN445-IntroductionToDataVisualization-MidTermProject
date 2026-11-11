"""
sidebar.py - Filter panel. render() draws the widgets and returns the filtered dataframe.

To add a filter: add a widget in render(), pass its value to apply_filters(), filter there.
"""

import math

import pandas as pd
import streamlit as st


def apply_filters(df: pd.DataFrame, leagues, season, goal_range, max_home_odds, comebacks_only) -> pd.DataFrame:
    out = df
    if leagues:
        out = out[out['league_name'].isin(leagues)]
    if season != "All Seasons":
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


def render(df_raw: pd.DataFrame) -> pd.DataFrame:
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/53/53283.png", width=64)
        st.title("⚽ Control Panel")
        st.caption("CEN445 - Exploratory Data Visualization")
        st.write("---")

        # Refresh button to clear any cached states
        if st.button("🔄 Reload & Reset Filters"):
            st.cache_data.clear()
            st.session_state.clear()
            st.rerun()

        # Filter 1: League Multiselect (Dropdown)
        all_leagues = sorted(df_raw['league_name'].unique().tolist())
        leagues = st.multiselect(
            "🏆 Select Leagues",
            options=all_leagues,
            default=all_leagues,
            key="selected_leagues_multiselect"
        )

        # Filter 2: Season Selector (Selectbox)
        all_seasons = ["All Seasons"] + sorted(df_raw['season'].unique().tolist(), reverse=True)
        season = st.selectbox("📅 Select Season", options=all_seasons)

        # Filter 3: Total Goals Range (Slider)
        min_goals, max_goals = int(df_raw['total_goals'].min()), int(df_raw['total_goals'].max())
        goal_range = st.slider(
            "🎯 Total Goals Range",
            min_value=min_goals,
            max_value=max_goals,
            value=(min_goals, max_goals)
        )

        # Filter 4: Max Home Odds (Slider) - upper bound follows the data so nothing is hidden by default
        odds_ceiling = float(math.ceil(df_raw['home_odds'].max()))
        max_home_odds = st.slider(
            "💰 Max Home Odds Filter",
            min_value=1.0,
            max_value=odds_ceiling,
            value=odds_ceiling,
            step=0.5
        )

        # Filter 5: Comebacks Only (Checkbox)
        comebacks_only = st.checkbox("🔥 Show Comebacks Only (HT Deficit -> FT Win)", value=False)

        st.write("---")
        st.markdown("ℹ️ **Dataset Metrics:**")
        st.markdown(f"- Total Loaded: **{len(df_raw):,}** matches")
        st.markdown(f"- Dimensions: **{df_raw.shape[1]} columns**")
        st.markdown(f"- Coverage: **{df_raw['league_name'].nunique()} Leagues, "
                    f"{df_raw['season'].nunique()} Seasons**")

    return apply_filters(df_raw, leagues, season, goal_range, max_home_odds, comebacks_only)
