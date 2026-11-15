"""
6. ADVANCED: Animated Bubble Chart (Sezon Boyunca Lig Eğilimleri)
Question: Do league trends hold through the season?

One bubble = one league in one month. X = home win % so far this season, Y = average goals
per match so far, colour = league, size = matches played so far. Press play (or drag the
month slider) to watch each league's running totals settle from August to May.

Season month comes from match_date: Aug = 1 ... May = 10; the few June matches count as May.
Running totals cover every match up to and including that month. With "All seasons" both
seasons are pooled by season month.

Click interaction:
  - Click a bubble -> draw that league's path from August to May (other leagues fade) and
    show how far it moved below. Click more bubbles to compare; click again to remove.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.charts import interaction
from src.theme import LEAGUE_COLORS, THEME_TEMPLATE

CHART_KEY = "season_bubbles_chart"
TRAILS = "season_bubbles_trails"     # session state: leagues whose path is drawn
MONTHS = ['Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May']
FRAME_MS = 800
TRANSITION_MS = 500
REFERENCE_LINE = 'rgba(100, 116, 139, 0.6)'
FADED = 0.2
HOVER = ("<b>%{customdata[1]}</b> · up to %{customdata[2]}<br>"
         "Home win %{x:.1f}% · %{y:.2f} goals per match<br>%{customdata[3]:,} matches"
         "<br><i>%{customdata[4]}</i><extra></extra>")


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
    return [values.min() - pad, values.max() + pad]


def _trail(cum: pd.DataFrame, league: str) -> go.Scatter:
    """A league's path from August to May, with the first and last month labelled."""
    path = cum[(cum['league_name'] == league)].dropna(subset=['home_win_pct'])
    labels = [m if i in (0, len(path) - 1) else '' for i, m in enumerate(path['month_name'])]
    return go.Scatter(
        x=path['home_win_pct'], y=path['avg_goals'], mode='lines+markers+text',
        line=dict(color=LEAGUE_COLORS.get(league), width=2, dash='dot'),
        marker=dict(size=7, color=LEAGUE_COLORS.get(league)),
        text=labels, textposition='bottom center', textfont=dict(size=10),
        customdata=[['league', league, m, n] for m, n in zip(path['month_name'], path['matches'])],
        hovertemplate=(f"<b>{league}</b> · %{{customdata[2]}}<br>Home win %{{x:.1f}}% · "
                       "%{y:.2f} goals · %{customdata[3]:,} matches<br><i>Click to remove this path</i>"
                       "<extra></extra>"),
        showlegend=False, unselected=dict(marker=dict(opacity=1)),
    )


def build(df: pd.DataFrame, trails=()) -> go.Figure:
    cum = running_totals(df)
    shown = cum.dropna(subset=['home_win_pct'])
    if shown.empty:
        raise ValueError("No matches in the current filter.")
    trails = [lg for lg in trails if lg in set(cum['league_name'])]
    cum = cum.assign(click='league', hint=cum['league_name'].map(
        lambda lg: "Click to remove its path" if lg in trails else "Click to draw its path Aug → May"))

    fig = px.scatter(
        cum, x='home_win_pct', y='avg_goals',
        size='matches', size_max=45,
        color='league_name', color_discrete_map=LEAGUE_COLORS,
        text='league_name',
        animation_frame='month_name', animation_group='league_name',
        category_orders={'month_name': MONTHS, 'league_name': list(LEAGUE_COLORS)},
        custom_data=['click', 'league_name', 'month_name', 'matches', 'hint'],
        labels={'home_win_pct': 'Home win % so far', 'avg_goals': 'Avg goals per match so far'},
        range_x=_padded(shown['home_win_pct'], 3),
        range_y=_padded(shown['avg_goals'], 0.15),
    )
    # Direct labels: eight league colours can't all be told apart by hue alone.
    # With paths drawn, the other leagues fade so the paths stand out.
    for trace in [*fig.data, *(t for f in fig.frames for t in f.data)]:
        opacity = FADED if trails and trace.name not in trails else 0.85
        trace.textposition = 'top center'
        trace.textfont = dict(size=11)
        trace.marker.opacity = opacity
        trace.marker.line = dict(width=1, color='rgba(255, 255, 255, 0.7)')
        trace.unselected = dict(marker=dict(opacity=opacity))
        trace.hovertemplate = HOVER

    for league in trails:   # static traces after the animated ones, so frames leave them alone
        fig.add_trace(_trail(cum, league))

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
        title=dict(text="6. League trends through the season", x=0, xanchor='left'),
        template=THEME_TEMPLATE,
        height=560,
        showlegend=False,
        dragmode=False,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    fig.update_xaxes(ticksuffix='%', fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _on_click(cd):
    if isinstance(cd, (list, tuple)) and len(cd) > 1 and cd[0] == 'league':
        trails = st.session_state.get(TRAILS, [])
        st.session_state[TRAILS] = [t for t in trails if t != cd[1]] if cd[1] in trails else trails + [cd[1]]


def _clear_trails():
    st.session_state[TRAILS] = []


def _movement_table(df: pd.DataFrame, trails: list):
    """How far each chosen league moved between its first month and May."""
    cum = running_totals(df).dropna(subset=['home_win_pct'])
    rows = []
    for league in trails:
        path = cum[cum['league_name'] == league]
        if path.empty:
            continue
        first, last = path.iloc[0], path.iloc[-1]
        rows.append({
            'League': league,
            f'Home win % ({first["month_name"]})': first['home_win_pct'],
            'Home win % (May)': last['home_win_pct'],
            'Change (pp)': last['home_win_pct'] - first['home_win_pct'],
            f'Avg goals ({first["month_name"]})': first['avg_goals'],
            'Avg goals (May)': last['avg_goals'],
            'Change (goals)': last['avg_goals'] - first['avg_goals'],
        })
    if rows:
        table = pd.DataFrame(rows).set_index('League')
        st.dataframe(table, width="stretch", column_config={
            c: st.column_config.NumberColumn(format="%+.1f" if c == 'Change (pp)' else
                                             "%+.2f" if c == 'Change (goals)' else
                                             "%.1f" if 'Home' in c else "%.2f")
            for c in table.columns})


def render(df: pd.DataFrame):
    trails = st.session_state.get(TRAILS, [])
    try:
        fig = build(df, trails)
    except ValueError as e:
        st.info(str(e))
        return
    interaction.plotly_chart(fig, CHART_KEY, _on_click)

    if trails:
        c1, c2 = st.columns([4, 1], vertical_alignment="center")
        c1.markdown("##### 🧭 How far each league moved")
        c2.button("✕ Clear paths", key="season_bubbles_clear", on_click=_clear_trails, type="tertiary")
        _movement_table(df, trails)
    st.caption(
        "Each bubble is one league's running total from August up to that month; bigger = more matches. "
        "**Press ▶** or drag the month slider. **Click a bubble** to draw that league's path from "
        "August to May; a short path means the early-season pattern held. Dashed lines = all shown "
        "matches over the full season. With *All seasons*, both seasons are pooled by month."
    )
