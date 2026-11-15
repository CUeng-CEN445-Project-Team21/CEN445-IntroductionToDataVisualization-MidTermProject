"""
6. ADVANCED: 2D Contour / Density Plot (Bahis Oranları Yoğunluk Yüzeyi)
Insight: Uncovers market odds clusters and identifies upset sweet-spots.

Every filtered match is used (no odds cut-off). Odds are on a log scale, and each result's
density is normalised on its own so large classes (home wins) don't dominate.

Click interaction (shared with charts 4 and 5, see linked.py):
  - Hover anywhere -> how often home wins / draws / away wins happen at those odds.
  - Click an area -> highlight the matches in that odds cell (outlined) in all three charts.
  - Highlighted matches from any chart appear here as dots; click a dot to pin that match
    (pinned matches are ringed here and drawn bold in chart 4).
  - Click a legend entry -> hide/show that result's rings and dots.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.charts import linked
from src.theme import COLOR_PALETTE, RESULT_COLORS, THEME_TEMPLATE

CHART_KEY = "odds_contour_chart"
ODDS_TICKS = [1.2, 1.5, 2, 3, 5, 8, 15, 30]
RESULT_ORDER = ['Home Win', 'Draw', 'Away Win']
RESULT_SYMBOLS = {'Home Win': 'circle', 'Draw': 'diamond', 'Away Win': 'triangle-up'}
BIG_FAVOURITE = 1.5   # home odds at or below this count as a big home favourite
HIGHLIGHT = COLOR_PALETTE['highlight']


def _cell_targets(d: pd.DataFrame) -> go.Scatter:
    """One invisible, clickable point per non-empty odds cell, with that cell's result split."""
    ci, cj = linked.cell_index(d['home_odds']), linked.cell_index(d['away_odds'])
    cells = pd.DataFrame({'i': ci, 'j': cj, 'ftr': d['ftr'].to_numpy()})
    counts = cells.groupby(['i', 'j'])['ftr'].value_counts().unstack(fill_value=0)
    counts = counts.reindex(columns=['H', 'D', 'A'], fill_value=0)
    chosen = linked.state()['cell']

    edges = np.log10(linked.CELL_EDGES)
    x, y, cd, hover = [], [], [], []
    for (i, j), row in counts.iterrows():
        n = int(row.sum())
        x.append((edges[i] + edges[i + 1]) / 2)
        y.append((edges[j] + edges[j + 1]) / 2)
        cd.append(['cell', int(i), int(j)])
        action = "remove this area" if chosen == (i, j) else "highlight these matches"
        hover.append(f"<b>{linked.cell_label(i, j).capitalize()}</b><br>{n:,} matches · "
                     f"Home win {row['H'] / n:.0%} · Draw {row['D'] / n:.0%} · Away win {row['A'] / n:.0%}"
                     f"<br><i>Click to {action}</i>")
    return go.Scatter(x=x, y=y, mode='markers', marker=dict(size=22, opacity=0),
                      customdata=cd, hovertext=hover, hovertemplate="%{hovertext}<extra></extra>",
                      showlegend=False, unselected=dict(marker=dict(opacity=0)),
                      selected=dict(marker=dict(opacity=0)))


def build(df: pd.DataFrame) -> go.Figure:
    d = df.dropna(subset=['home_odds', 'away_odds'])
    if d.empty:
        fig = go.Figure()
        fig.update_layout(title=dict(text="🌌 6. Where each result sits in odds space — no matches",
                                     x=0, xanchor='left'), template=THEME_TEMPLATE, height=520)
        return fig

    d = d.assign(x=np.log10(d['home_odds']), y=np.log10(d['away_odds']))
    lo, hi = min(d['x'].min(), d['y'].min()), max(d['x'].max(), d['y'].max())
    ticks = [t for t in ODDS_TICKS if lo <= np.log10(t) <= hi] or ODDS_TICKS
    axis_fmt = dict(tickvals=np.log10(ticks), ticktext=[f"{t:g}" for t in ticks], fixedrange=True)

    fig = px.density_contour(
        d, x='x', y='y',
        color='result_label', color_discrete_map=RESULT_COLORS,
        category_orders={'result_label': RESULT_ORDER},
        histnorm='probability density',
        nbinsx=35, nbinsy=35,
    )
    fig.update_traces(contours_coloring="none", showscale=False, line_width=2, ncontours=6,
                      hoverinfo='skip', hovertemplate=None)

    # Clickable cells go under the match dots, so a dot wins when both are under the cursor.
    fig.add_trace(_cell_targets(d))

    chosen = linked.state()['cell']
    if chosen:
        i, j = chosen
        e = np.log10(linked.CELL_EDGES)
        fig.add_shape(type='rect', x0=e[i], x1=e[i + 1], y0=e[j], y1=e[j + 1],
                      line=dict(color=HIGHLIGHT, width=2.5), fillcolor='rgba(16, 185, 129, 0.12)')

    # ── Highlighted and pinned matches as dots ────────────────────────────
    pinned = d['id'].isin(linked.pins())
    if linked.active() or pinned.any():
        sel = d[(linked.mask(d) if linked.active() else False) | pinned]
        n_sel = len(sel) - int(pinned.sum())
        size, opacity = (9, 0.9) if n_sel <= 60 else (6, 0.6) if n_sel <= 400 else (4, 0.35)
        for result in RESULT_ORDER:
            sub = sel[sel['result_label'] == result]
            if sub.empty:
                continue
            is_picked = sub['id'].isin(linked.pins()).to_numpy()
            fig.add_trace(go.Scatter(
                x=sub['x'], y=sub['y'], mode='markers', name=result, legendgroup=result,
                showlegend=False,
                marker=dict(size=np.where(is_picked, 16, size), opacity=np.where(is_picked, 1, opacity),
                            color=RESULT_COLORS[result], symbol=RESULT_SYMBOLS[result],
                            line=dict(width=np.where(is_picked, 3, 0.5),
                                      color=np.where(is_picked, HIGHLIGHT, 'rgba(255,255,255,0.6)'))),
                customdata=np.column_stack([
                    np.full(len(sub), 'pin'), sub['id'], sub['home_team'], sub['away_team'],
                    sub['fthg'], sub['ftag'], sub['match_date'].astype(str), sub['league_name'],
                    sub['home_odds'], sub['away_odds'],
                    np.where(is_picked, "📌 Pinned · click to unpin", "Click to pin and follow it in chart 4"),
                ]).tolist(),
                hovertemplate=("<b>%{customdata[2]} %{customdata[4]}–%{customdata[5]} %{customdata[3]}</b>"
                               "<br>%{customdata[6]} · %{customdata[7]}"
                               "<br>Odds: home %{customdata[8]} · away %{customdata[9]}"
                               "<br><i>%{customdata[10]}</i><extra></extra>"),
                unselected=dict(marker=dict(opacity=opacity)),
            ))

    fig.update_xaxes(title="Home closing odds (log scale)", **axis_fmt)
    fig.update_yaxes(title="Away closing odds (log scale)", **axis_fmt)
    fig.update_layout(
        title=dict(text="🌌 6. Where each result sits in odds space", x=0, xanchor='left'),
        template=THEME_TEMPLATE,
        height=520,
        hovermode='closest',
        dragmode=False,
        legend=dict(title_text="", orientation='h', x=0, xanchor='left', y=1.0, yanchor='bottom'),
        margin=dict(l=10, r=10, t=80, b=10),
    )
    return fig


def render(df: pd.DataFrame):
    linked.plotly_chart(build(df), CHART_KEY)

    notes = []
    chosen = linked.state()['cell']
    if chosen:
        i, j = chosen
        in_cell = df[(linked.cell_index(df['home_odds']) == i) & (linked.cell_index(df['away_odds']) == j)]
        if len(in_cell):
            r = in_cell['ftr'].value_counts(normalize=True)
            notes.append(f"**Selected area** ({linked.cell_label(i, j)}): {len(in_cell):,} matches — "
                         f"home win {r.get('H', 0):.0%}, draw {r.get('D', 0):.0%}, away win {r.get('A', 0):.0%}.")
    fav = df[df['home_odds'] <= BIG_FAVOURITE]
    if len(fav) >= 30:
        notes.append(f"With home odds ≤ {BIG_FAVOURITE}, away teams won {(fav['ftr'] == 'A').mean():.0%} "
                     f"of {len(fav):,} matches.")
    notes.append("**Hover** for the result split at any odds, **click an area** to highlight those matches "
                 "in charts 4–6, click a legend entry to hide a result. Each result's rings are normalised "
                 "on their own, so compare where they sit, not how many there are.")
    st.caption(" ".join(notes))
