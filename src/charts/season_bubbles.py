"""
6. ADVANCED: Animated Bubble Chart (Sezon Boyunca Lig Eğilimleri)
Question: Do league trends hold through the season?

One bubble = one league in one month. X = home win % so far this season, Y = average goals
per match so far, colour = league, size = matches played so far. Press play (or drag the
month slider) to watch each league's running totals settle from August to May.

Season month comes from match_date: Aug = 1 ... May = 10; the few June matches count as May.
Running totals cover every match up to and including that month. With "All seasons" both
seasons are pooled by season month.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.theme import LEAGUE_COLORS, THEME_TEMPLATE

MONTHS = ['Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May']
FRAME_MS = 800
TRANSITION_MS = 500
REFERENCE_LINE = 'rgba(100, 116, 139, 0.6)'


def season_month(dates: pd.Series) -> pd.Series:
    """Aug = 1 ... May = 10. June folds into May, July (pre-season) into August."""
    m = (pd.to_datetime(dates).dt.month - 8) % 12 + 1      # Aug=1 ... Jul=12
    return m.where(m != 12, 1).clip(upper=len(MONTHS))


def running_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Per league and season month: matches, home win % and avg goals over all matches so far."""
    d = df.assign(month=season_month(df['match_date']), home_win=(df['ftr'] == 'H').astype(int))
    monthly = d.groupby(['league_name', 'month']).agg(
        matches=('id', 'size'), home_wins=('home_win', 'sum'), goals=('total_goals', 'sum'))

    # Every league in every month, so no bubble drops out of the animation.
    grid = pd.MultiIndex.from_product([sorted(d['league_name'].unique()), range(1, len(MONTHS) + 1)],
                                      names=['league_name', 'month'])
    cum = monthly.reindex(grid, fill_value=0).groupby(level='league_name').cumsum().reset_index()

    played = cum['matches'].where(cum['matches'] > 0)        # NaN before a league's first match
    cum['home_win_pct'] = (cum['home_wins'] / played * 100).round(1)
    cum['avg_goals'] = (cum['goals'] / played).round(2)
    cum['month_name'] = cum['month'].map(lambda m: MONTHS[m - 1])
    return cum


def _padded(values: pd.Series, pad: float) -> list:
    lo, hi = values.min(), values.max()
    return [lo - pad, hi + pad]


def build(df: pd.DataFrame) -> go.Figure:
    cum = running_totals(df)
    shown = cum.dropna(subset=['home_win_pct'])
    if shown.empty:
        raise ValueError("No matches in the current filter.")

    fig = px.scatter(
        cum, x='home_win_pct', y='avg_goals',
        size='matches', size_max=45,
        color='league_name', color_discrete_map=LEAGUE_COLORS,
        text='league_name',
        animation_frame='month_name', animation_group='league_name',
        category_orders={'month_name': MONTHS, 'league_name': list(LEAGUE_COLORS)},
        hover_name='league_name',
        hover_data={'month_name': True, 'matches': ':,', 'home_win_pct': ':.1f',
                    'avg_goals': ':.2f', 'league_name': False},
        labels={'home_win_pct': 'Home win % so far', 'avg_goals': 'Avg goals per match so far',
                'matches': 'Matches so far', 'month_name': 'Month', 'league_name': 'League'},
        range_x=_padded(shown['home_win_pct'], 3),
        range_y=_padded(shown['avg_goals'], 0.15),
    )
    # Direct labels: eight league colours can't all be told apart by hue alone.
    fig.update_traces(textposition='top center', textfont=dict(size=11),
                      marker=dict(line=dict(width=1, color='rgba(255, 255, 255, 0.7)'), opacity=0.85))
    for frame in fig.frames:
        for trace in frame.data:
            trace.textposition = 'top center'

    # Dashed reference lines: where all shown matches end up after the full season.
    total = cum[cum['month'] == len(MONTHS)][['matches', 'home_wins', 'goals']].sum()
    final_hw, final_goals = total['home_wins'] / total['matches'] * 100, total['goals'] / total['matches']
    fig.add_vline(x=final_hw, line=dict(color=REFERENCE_LINE, dash='dash', width=1))
    fig.add_hline(y=final_goals, line=dict(color=REFERENCE_LINE, dash='dash', width=1),
                  annotation_text=f"Full season: {final_hw:.1f}% home wins · {final_goals:.2f} goals",
                  annotation_position='bottom right', annotation_font_size=11)

    play = fig.layout.updatemenus[0].buttons[0].args[1]
    play['frame']['duration'] = FRAME_MS
    play['transition']['duration'] = TRANSITION_MS
    fig.layout.sliders[0].currentvalue.prefix = "Month: "

    fig.update_layout(
        title=dict(text="🫧 6. League trends through the season", x=0, xanchor='left'),
        template=THEME_TEMPLATE,
        height=560,
        showlegend=False,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    fig.update_xaxes(ticksuffix='%')
    return fig


def render(df: pd.DataFrame):
    try:
        fig = build(df)
    except ValueError as e:
        st.info(str(e))
        return
    st.plotly_chart(fig, width="stretch", config={'displaylogo': False})
    st.caption(
        "Each bubble is one league's running total from August up to that month; bigger = more matches "
        "played. **Press ▶** or drag the month slider. Bubbles that barely move after the autumn mean "
        "the league's early-season pattern held. Dashed lines = all shown matches over the full season. "
        "With *All seasons*, both seasons are pooled by month."
    )
