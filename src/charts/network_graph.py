"""
5. ADVANCED: Network Graph (Takımlar Arası Üstünlük Ağı)
Question: Among a league's top teams, who beats whom?

Node = one of the top 8 teams of the selected league (most wins, home + away combined).
Arrow A -> B = A beat B; arrow width = how many times A beat B. A pairing where both teams
won at least once gets two arrows, drawn side by side. Node colour = net wins inside the
group (wins - losses against the other 7, diverging), node size = wins inside the group.

Click interaction:
  - Click a team -> pin it (shared with chart 4). Its arrows light up (teal = teams it beats,
    purple = teams that beat it), the rest fades, and its record vs the group appears below.
  - Click an arrow -> focus that head-to-head and list every game between the two teams.
  - Click the same team / arrow again to clear it.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.charts import interaction
from src.theme import COLOR_PALETTE, THEME_TEMPLATE

CHART_KEY = "network_graph_chart"
PAIR = "network_graph_pair"     # session state: the focused head-to-head (sorted team pair) or None
TOP_N = 8

# Diverging scale for net wins: purple (beaten by the group) -> slate (even) -> teal (beats it).
# Deliberately not blue/red: those mean home/away win everywhere else on the dashboard.
NET_COLORSCALE = [[0, '#9333EA'], [0.5, '#94A3B8'], [1, '#0D9488']]
ARROW_COLOR = 'rgba(100, 116, 139, 0.55)'    # slate, readable on light and dark backgrounds
ARROW_DIM = 'rgba(100, 116, 139, 0.12)'
BEATS_COLOR = 'rgba(13, 148, 136, 0.9)'      # teal: the pinned team won these
BEATEN_COLOR = 'rgba(147, 51, 234, 0.85)'    # purple: the pinned team lost these
FOCUS = COLOR_PALETTE['highlight']
NODE_MIN, NODE_MAX = 16, 46                   # marker diameter in px
SIDE_OFFSET = 0.035                           # gap between the two arrows of one pairing


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


def _arrow_style(a: str, b: str, wins: int, pinned: set, pair: tuple | None):
    """Colour and width of the arrow a -> b, given what is focused."""
    width = 0.8 + 1.1 * wins
    if pair:
        return (FOCUS, width + 1) if {a, b} == set(pair) else (ARROW_DIM, width)
    if pinned:
        if a in pinned and b in pinned:
            return FOCUS, width + 1
        if a in pinned:
            return BEATS_COLOR, width + 1
        if b in pinned:
            return BEATEN_COLOR, width + 1
        return ARROW_DIM, width
    return ARROW_COLOR, width


def build(df: pd.DataFrame, league: str, pinned=(), pair: tuple | None = None):
    sub = df[df['league_name'] == league]
    teams = top_teams(sub)
    if len(teams) < 3:
        raise ValueError(f"{league} has fewer than 3 teams with a win in the current filter, "
                         "so there is no network to draw. Broaden the sidebar filters.")
    pair_wins, record, n_games = group_record(sub, teams)
    pinned = set(pinned) & set(teams)
    pair = pair if pair and set(pair) <= set(teams) else None
    focus = set(pair) if pair else pinned

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
    hx, hy, htext, hdata = [], [], [], []
    connected = set()
    for (a, b), wins in sorted(pair_wins.items(), key=lambda kv: kv[1]):   # thick arrows on top
        color, width = _arrow_style(a, b, wins, pinned, pair)
        if focus & {a, b}:
            connected |= {a, b}
        p0, p1 = pos[a], pos[b]
        direction = (p1 - p0) / np.linalg.norm(p1 - p0)
        # Shift each arrow to its own right-hand side so A->B and B->A sit next to each other.
        shift = np.array([direction[1], -direction[0]]) * SIDE_OFFSET
        (x0, y0), (x1, y1) = p0 + shift, p1 + shift
        fig.add_annotation(
            x=x1, y=y1, ax=x0, ay=y0, xref='x', yref='y', axref='x', ayref='y',
            text='', showarrow=True, arrowhead=2, arrowsize=1,
            arrowwidth=width, arrowcolor=color,
            standoff=size[b] / 2 + 2, startstandoff=size[a] / 2 + 2,
        )
        # Invisible markers along the arrow carry its hover text and make it clickable.
        lost = pair_wins.get((b, a), 0)
        action = "clear" if pair and {a, b} == set(pair) else "see their games"
        for t in (0.35, 0.5, 0.65):
            hx.append(x0 + t * (x1 - x0))
            hy.append(y0 + t * (y1 - y0))
            htext.append(f"<b>{a}</b> beat <b>{b}</b> {wins}×<br>({b} won {lost}×)"
                         f"<br><i>Click to {action}</i>")
            hdata.append(['pair', a, b])

    fig.add_trace(go.Scatter(
        x=hx, y=hy, mode='markers', marker=dict(size=14, opacity=0),
        customdata=hdata, hovertext=htext, hoverinfo='text', showlegend=False,
        unselected=dict(marker=dict(opacity=0)), selected=dict(marker=dict(opacity=0)),
    ))

    # ── Nodes ─────────────────────────────────────────────────────────────
    rec = record.loc[ranked]
    if focus:
        opacity = [1.0 if t in focus else 0.75 if t in connected else 0.25 for t in ranked]
    else:
        opacity = [1.0] * n
    hint = ["📌 Pinned · click to unpin" if t in pinned else "Click to pin (also shows in chart 4)"
            for t in ranked]
    fig.add_trace(go.Scatter(
        x=[pos[t][0] for t in ranked], y=[pos[t][1] for t in ranked],
        mode='markers+text',
        text=[f"<b>{t}</b> {r.net:+d}" if r.net else f"<b>{t}</b> 0" for t, r in rec.iterrows()],
        textposition=[_label_position(angle[t]) for t in ranked],
        textfont=dict(size=12),
        customdata=[['team', t, int(r.W), int(r.D), int(r.L), int(r.net), h]
                    for (t, r), h in zip(rec.iterrows(), hint)],
        hovertemplate="<b>%{customdata[1]}</b><br>"
                      f"vs the other {n - 1}: "
                      "%{customdata[2]} W · %{customdata[3]} D · %{customdata[4]} L"
                      "<br>Net wins: %{customdata[5]:+d}<br><i>%{customdata[6]}</i><extra></extra>",
        marker=dict(
            size=[size[t] + (6 if t in focus else 0) for t in ranked],
            color=rec['net'], colorscale=NET_COLORSCALE, cmid=0, opacity=opacity,
            showscale=True,
            colorbar=dict(title=dict(text="Net wins"), thickness=10, len=0.6, x=1.0),
            line=dict(width=[4 if t in focus else 1.5 for t in ranked],
                      color=[FOCUS if t in focus else 'rgba(148, 163, 184, 0.9)' for t in ranked]),
        ),
        unselected=dict(marker=dict(opacity=1)),
        showlegend=False,
    ))

    title = f"🕸️ 5. Who beats whom · {league} top {n}"
    if pair:
        title += f" · 🔍 {pair[0]} vs {pair[1]}"
    fig.update_layout(
        title=dict(text=title, x=0, xanchor='left'),
        template=THEME_TEMPLATE,
        showlegend=False,
        hovermode='closest',
        dragmode=False,
        height=520,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(visible=False, range=[-1.9, 1.9], fixedrange=True),
        yaxis=dict(visible=False, range=[-1.35, 1.35], fixedrange=True),
    )
    return fig, n_games, ranked, record, pair_wins


# ── Clicks and detail cards ──────────────────────────────────────────────────────────────────

def _on_click(cd):
    if not isinstance(cd, (list, tuple)) or not cd:
        return
    if cd[0] == 'team':
        interaction.toggle_team(cd[1])
        st.session_state[PAIR] = None
    elif cd[0] == 'pair':
        pair = tuple(sorted(cd[1:3]))
        st.session_state[PAIR] = None if st.session_state.get(PAIR) == pair else pair


def _clear_pair():
    st.session_state[PAIR] = None


def _team_card(team: str, teams: list, record: pd.DataFrame, pair_wins: dict):
    row = record.loc[team]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Wins", int(row['W']))
    m2.metric("Draws", int(row['D']))
    m3.metric("Losses", int(row['L']))
    m4.metric("Net", f"{int(row['net']):+d}")
    rows = []
    for other in teams:
        if other == team:
            continue
        w, l = pair_wins.get((team, other), 0), pair_wins.get((other, team), 0)
        rows.append(dict(Opponent=other, Wins=w, Losses=l, Net=w - l,
                         Verdict='✅ Dominates' if w > l else ('❌ Dominated' if w < l else '🤝 Even')))
    table = pd.DataFrame(rows).sort_values('Net', ascending=False).set_index('Opponent')
    st.dataframe(table, width="stretch")


def _pair_card(df: pd.DataFrame, league: str, a: str, b: str):
    games = df[(df['league_name'] == league) &
               (((df['home_team'] == a) & (df['away_team'] == b)) |
                ((df['home_team'] == b) & (df['away_team'] == a)))].sort_values('match_date')
    wins_a = int((((games['home_team'] == a) & (games['ftr'] == 'H')) |
                  ((games['away_team'] == a) & (games['ftr'] == 'A'))).sum())
    draws = int((games['ftr'] == 'D').sum())
    c1, c2 = st.columns([4, 1], vertical_alignment="center")
    c1.markdown(f"##### 🔍 {a} vs {b} — {len(games)} games")
    c2.button("✕ Close", key="network_close_pair", on_click=_clear_pair, type="tertiary")
    m1, m2, m3 = st.columns(3)
    m1.metric(f"{a} wins", wins_a)
    m2.metric("Draws", draws)
    m3.metric(f"{b} wins", len(games) - wins_a - draws)
    st.dataframe(
        games.assign(Score=games['fthg'].astype(str) + '–' + games['ftag'].astype(str))
             [['match_date', 'season', 'home_team', 'Score', 'away_team']]
             .rename(columns={'match_date': 'Date', 'season': 'Season', 'home_team': 'Home',
                              'away_team': 'Away'}),
        width="stretch", hide_index=True,
    )


def render(df: pd.DataFrame):
    leagues = sorted(df['league_name'].unique())
    league = st.selectbox(
        "League", leagues,
        index=leagues.index('Premier League') if 'Premier League' in leagues else 0,
        key="network_graph_league", on_change=_clear_pair,
    )
    pinned = interaction.pinned_teams()
    try:
        fig, n_games, teams, record, pair_wins = build(df, league, pinned, st.session_state.get(PAIR))
    except ValueError as e:
        st.info(str(e))
        return

    interaction.plotly_chart(fig, CHART_KEY, _on_click)

    pair = st.session_state.get(PAIR)
    shown = [t for t in pinned if t in teams]
    if pair and set(pair) <= set(teams):
        _pair_card(df, league, *pair)
    elif shown:
        st.markdown("##### 📌 Record vs this group")
        tabs = st.tabs(shown) if len(shown) > 1 else [st.container()]
        for team, tab in zip(shown, tabs):
            with tab:
                if len(shown) == 1:
                    st.caption(f"**{team}**")
                _team_card(team, teams, record, pair_wins)
        st.button("✕ Unpin these teams", key="network_unpin", type="tertiary",
                  on_click=lambda: [interaction.toggle_team(t) for t in shown])

    st.caption(
        "**Click a team** to pin it: teal arrows = teams it beats, purple = teams that beat it "
        "(it is pinned in chart 4 too). **Click an arrow** for that head-to-head's games. "
        "Arrow A → B = A beat B, thicker = more wins; number and colour = wins minus losses against "
        f"this group; bigger node = more wins. {n_games:,} games among these teams; draws carry no arrow."
    )
