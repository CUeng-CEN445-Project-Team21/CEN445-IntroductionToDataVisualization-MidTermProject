"""
5. ADVANCED: Network Graph (Takımlar Arası Üstünlük Ağı)
Question: Among a league's top teams, who beats whom?

Node = one of the top 8 teams of the selected league (most wins, home + away combined).
Arrow A -> B = A beat B; arrow width = how many times A beat B. A pairing where both teams
won at least once gets two arrows, drawn side by side. Node colour = net wins inside the
group (wins - losses against the other 7, diverging), node size = wins inside the group.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.theme import THEME_TEMPLATE

TOP_N = 8

# Diverging scale for net wins: purple (beaten by the group) -> slate (even) -> teal (beats it).
# Deliberately not blue/red: those mean home/away win everywhere else on the dashboard.
NET_COLORSCALE = [[0, '#9333EA'], [0.5, '#94A3B8'], [1, '#0D9488']]
ARROW_COLOR = 'rgba(100, 116, 139, 0.55)'   # slate, readable on light and dark backgrounds
NODE_MIN, NODE_MAX = 16, 46                  # marker diameter in px
SIDE_OFFSET = 0.035                          # gap between the two arrows of one pairing


def top_teams(sub: pd.DataFrame, top_n: int = TOP_N) -> list:
    """Top N teams by total wins (home + away). Ties: better goal difference, then name."""
    home = pd.DataFrame({'team': sub['home_team'], 'win': sub['ftr'] == 'H',
                         'gd': sub['fthg'] - sub['ftag']})
    away = pd.DataFrame({'team': sub['away_team'], 'win': sub['ftr'] == 'A',
                         'gd': sub['ftag'] - sub['fthg']})
    t = pd.concat([home, away]).groupby('team').agg(wins=('win', 'sum'), gd=('gd', 'sum'))
    t = t[t['wins'] > 0].reset_index()
    return t.sort_values(['wins', 'gd', 'team'], ascending=[False, False, True])['team'].head(top_n).tolist()


def group_record(sub: pd.DataFrame, teams: list):
    """Wins of A over B for every ordered pair, and W / D / L per team, inside the group."""
    games = sub[sub['home_team'].isin(teams) & sub['away_team'].isin(teams)]
    decided = games[games['ftr'] != 'D']
    home_won = decided['ftr'] == 'H'
    winner = np.where(home_won, decided['home_team'], decided['away_team'])
    loser = np.where(home_won, decided['away_team'], decided['home_team'])
    pair_wins = pd.Series(list(zip(winner, loser)), dtype=object).value_counts().to_dict()

    draws = games[games['ftr'] == 'D']
    record = pd.DataFrame({
        'W': pd.Series(winner).value_counts(),
        'D': pd.concat([draws['home_team'], draws['away_team']]).value_counts(),
        'L': pd.Series(loser).value_counts(),
    }).reindex(teams).fillna(0).astype(int)
    record['net'] = record['W'] - record['L']
    return pair_wins, record, len(games)


def _label_position(angle: float) -> str:
    """Put each label on the outside of the circle so it never covers arrows or nodes."""
    x, y = np.cos(angle), np.sin(angle)
    if x > 0.35:
        return 'middle right'
    if x < -0.35:
        return 'middle left'
    return 'top center' if y > 0 else 'bottom center'


def build(df: pd.DataFrame, league: str) -> tuple[go.Figure, int]:
    sub = df[df['league_name'] == league]
    teams = top_teams(sub)
    if len(teams) < 3:
        raise ValueError(f"{league} has fewer than 3 teams with a win in the current filter, "
                         "so there is no network to draw. Broaden the sidebar filters.")
    pair_wins, record, n_games = group_record(sub, teams)

    # Circular layout: strongest team (net wins) at the top, then alternating right / left downwards.
    ranked = record.sort_values(['net', 'W'], ascending=False).index.tolist()
    n = len(ranked)
    slot = {t: 0 if r == 0 else ((r + 1) // 2 if r % 2 else n - r // 2) for r, t in enumerate(ranked)}
    angle = {t: np.pi / 2 - 2 * np.pi * slot[t] / n for t in ranked}
    pos = {t: np.array([np.cos(a), np.sin(a)]) for t, a in angle.items()}

    max_w = max(int(record['W'].max()), 1)
    size = {t: NODE_MIN + (NODE_MAX - NODE_MIN) * np.sqrt(record.at[t, 'W'] / max_w) for t in ranked}

    fig = go.Figure()

    # ── Arrows: one per direction with at least one win ─────────────────────
    hx, hy, htext = [], [], []
    for (a, b), wins in sorted(pair_wins.items(), key=lambda kv: kv[1]):   # thick arrows on top
        p0, p1 = pos[a], pos[b]
        direction = (p1 - p0) / np.linalg.norm(p1 - p0)
        # Shift each arrow to its own right-hand side so A->B and B->A sit next to each other.
        shift = np.array([direction[1], -direction[0]]) * SIDE_OFFSET
        (x0, y0), (x1, y1) = p0 + shift, p1 + shift
        fig.add_annotation(
            x=x1, y=y1, ax=x0, ay=y0, xref='x', yref='y', axref='x', ayref='y',
            text='', showarrow=True, arrowhead=2, arrowsize=1,
            arrowwidth=0.8 + 1.1 * wins, arrowcolor=ARROW_COLOR,
            standoff=size[b] / 2 + 2, startstandoff=size[a] / 2 + 2,
        )
        # Invisible markers along the arrow carry its hover text.
        lost = pair_wins.get((b, a), 0)
        for t in (0.35, 0.5, 0.65):
            hx.append(x0 + t * (x1 - x0))
            hy.append(y0 + t * (y1 - y0))
            htext.append(f"<b>{a}</b> beat <b>{b}</b> {wins}×<br>({b} won {lost}×)")

    fig.add_trace(go.Scatter(
        x=hx, y=hy, mode='markers', marker=dict(size=12, opacity=0),
        hovertext=htext, hoverinfo='text', showlegend=False,
    ))

    # ── Nodes ─────────────────────────────────────────────────────────────
    rec = record.loc[ranked]
    others = n - 1
    fig.add_trace(go.Scatter(
        x=[pos[t][0] for t in ranked], y=[pos[t][1] for t in ranked],
        mode='markers+text',
        text=[f"<b>{t}</b> {r.net:+d}" if r.net else f"<b>{t}</b> 0" for t, r in rec.iterrows()],
        textposition=[_label_position(angle[t]) for t in ranked],
        textfont=dict(size=12),
        customdata=rec[['W', 'D', 'L', 'net']].to_numpy(),
        hovertemplate="<b>%{hovertext}</b><br>"
                      f"vs the other {others}: "
                      "%{customdata[0]} W · %{customdata[1]} D · %{customdata[2]} L"
                      "<br>Net wins: %{customdata[3]:+d}<extra></extra>",
        hovertext=ranked,
        marker=dict(
            size=[size[t] for t in ranked],
            color=rec['net'], colorscale=NET_COLORSCALE, cmid=0,
            showscale=True,
            colorbar=dict(title=dict(text="Net wins"), thickness=10, len=0.6, x=1.0),
            line=dict(width=1.5, color='rgba(148, 163, 184, 0.9)'),
        ),
        showlegend=False,
    ))

    fig.update_layout(
        title=dict(text=f"🕸️ 5. Who beats whom · {league} top {n}", x=0, xanchor='left'),
        template=THEME_TEMPLATE,
        showlegend=False,
        hovermode='closest',
        dragmode=False,
        height=520,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(visible=False, range=[-1.9, 1.9], fixedrange=True),
        yaxis=dict(visible=False, range=[-1.35, 1.35], fixedrange=True),
    )
    return fig, n_games


def render(df: pd.DataFrame):
    leagues = sorted(df['league_name'].unique())
    league = st.selectbox(
        "League", leagues,
        index=leagues.index('Premier League') if 'Premier League' in leagues else 0,
        key="network_graph_league",
    )
    try:
        fig, n_games = build(df, league)
    except ValueError as e:
        st.info(str(e))
        return

    st.plotly_chart(fig, width="stretch", config={'displaylogo': False})
    st.caption(
        "Arrow A → B = A beat B; thicker = more wins in that pairing. Two arrows side by side mean both "
        "teams won at least once. Number and colour = wins minus losses against the rest of this group "
        f"(teal beats the group, purple is beaten by it); bigger node = more wins. {n_games:,} games "
        "among these teams; draws carry no arrow. Hover a team or an arrow for the record."
    )
