"""
4. ADVANCED: Parallel Coordinates (Takımların İstatistik Profili)
Question: What does each team's full statistical profile look like?

One line = one team. Seven axes, left to right: points per game, goals scored / match,
goals conceded / match, win %, draw %, clean-sheet %, BTTS %. Line colour = points per game
(diverging: blue below the average team, red above it).
Team stats come from a long table with one row per team per match (home side: goals for =
fthg, against = ftag; away side the reverse).

Drawn by a small custom component (parallel_coordinates.js, on a canvas) instead of Plotly
parcoords, which has no hover and no click events in Streamlit. build() returns the
component's data, not a Plotly figure.

Interaction (all clicks and hovers):
  - Hover a line -> it is drawn bold, the rest fades, and its value shows on every axis.
  - Click a line -> pin the team (stays bold and labelled). Pinned teams are shared with
    chart 5. Click again to unpin.
  - Click a bar on an axis -> highlight the teams in that range (same axis = OR, different
    axes = AND); the green marks then show where those teams sit on every other axis.
  - Click a league pill -> only that league's teams.
"""

from pathlib import Path
from typing import NamedTuple

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v2 as components
from plotly.colors import sample_colorscale

from src.charts import interaction
from src.theme import COLOR_PALETTE

CHART_KEY = "parallel_coordinates_chart"
BINS = "parallel_coordinates_bins"     # session state: {axis key: [chosen bin indices]}
MIN_MATCHES = 15   # same cut-off as ML1; every team has 15+ matches under the default filters

# Diverging scale for points per game: blue = below the average team, red = above it, and
# the middle is the average. In dark mode the middle is white. In light mode it is a pale
# warm grey, because white lines vanish on the cream page. The component picks the set that
# matches the page.
# Saturated quarter stops keep the colour vivid on the way to the middle instead of fading
# to grey.
PPG_COLORSCALE_LIGHT = [[0, '#0B4FE0'], [0.25, '#3D86F5'], [0.5, '#C9C3B6'],
                        [0.75, '#F5553D'], [1, '#D90F1F']]
PPG_COLORSCALE_DARK = [[0, '#2E86FF'], [0.25, '#7AB8FF'], [0.5, '#FFFFFF'],
                       [0.75, '#FF8A70'], [1, '#FF3B30']]

_HERE = Path(__file__).parent
_COMPONENT = components.component(
    "cen445_parallel_coordinates",
    css=(_HERE / "parallel_coordinates.css").read_text(encoding="utf-8"),
    js=(_HERE / "parallel_coordinates.js").read_text(encoding="utf-8"),
)


class Axis(NamedTuple):
    key: str
    label: str
    pct: bool          # shown as a percentage
    edges: np.ndarray  # fixed bin edges, so a chosen bin means the same thing whatever the filter

    def fmt(self, v: float) -> str:
        return f"{v:.0f}%" if self.pct else f"{v:.2f}"

    def edge(self, v: float) -> str:
        return f"{v:g}%" if self.pct else f"{v:g}"

    def bins(self, values: np.ndarray) -> np.ndarray:
        return np.clip(np.searchsorted(self.edges, values, side='right') - 1, 0, len(self.edges) - 2)

    def bin_label(self, j: int) -> str:
        return f"{self.edge(self.edges[j])}–{self.edge(self.edges[j + 1])}"


_GOALS = np.arange(0, 4.01, 0.5)
_PCT10 = np.arange(0, 100.1, 10)
AXES = (
    Axis('ppg',             'Points / game',          False, np.arange(0, 3.01, 0.5)),
    Axis('scored_pm',       'Goals scored / match',   False, _GOALS),
    Axis('conceded_pm',     'Goals conceded / match', False, _GOALS),
    Axis('win_pct',         'Win %',                  True,  _PCT10),
    Axis('draw_pct',        'Draw %',                 True,  np.arange(0, 100.1, 5)),
    Axis('clean_sheet_pct', 'Clean-sheet %',          True,  _PCT10),
    Axis('btts_pct',        'BTTS %',                 True,  _PCT10),
)
AXIS_BY_KEY = {a.key: a for a in AXES}


# ── Data ─────────────────────────────────────────────────────────────────────────────────────

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
    return t.sort_values('ppg')       # weakest first, so the best teams are drawn on top


# ── Click state ──────────────────────────────────────────────────────────────────────────────

def chosen_bins() -> dict:
    return st.session_state.setdefault(BINS, {})


def toggle_bin(key: str, j: int):
    chosen = set(chosen_bins().get(key, ())) ^ {j}
    if chosen:
        chosen_bins()[key] = sorted(chosen)
    else:
        chosen_bins().pop(key, None)


def clear_bins(key: str | None = None):
    if key:
        chosen_bins().pop(key, None)
    else:
        st.session_state[BINS] = {}


def highlight_mask(teams: pd.DataFrame) -> np.ndarray:
    """True for every team inside all chosen bins (all True if nothing is chosen)."""
    keep = np.ones(len(teams), bool)
    for key, chosen in chosen_bins().items():
        axis = AXIS_BY_KEY[key]
        keep &= np.isin(axis.bins(teams[key].to_numpy(float)), chosen)
    return keep


# ── Component data ───────────────────────────────────────────────────────────────────────────

def _axes_payload(teams: pd.DataFrame, picked: np.ndarray, selecting: bool):
    """Each axis's ticks and bars, plus every team's 0..1 position on it."""
    axes, ys = [], []
    names = teams.index.to_numpy()
    for axis in AXES:
        v = teams[axis.key].to_numpy(float)
        b = axis.bins(v)
        lo_j, hi_j = int(b.min()), int(b.max()) + 1          # only the bins the data covers
        lo, hi = axis.edges[lo_j], axis.edges[hi_j]
        ys.append((v - lo) / (hi - lo))

        chosen = chosen_bins().get(axis.key, ())
        total = np.bincount(b, minlength=len(axis.edges))
        sel = np.bincount(b[picked], minlength=len(axis.edges)) if selecting else np.zeros_like(total)
        biggest = max(total.max(), 1)
        bars = []
        for j in range(lo_j, hi_j):
            in_bin = names[b == j][::-1]                      # best first (teams are sorted by ppg)
            body = [f"{total[j]} team{'s' if total[j] != 1 else ''}"]
            if total[j]:
                body.append("Top: " + ", ".join(in_bin[:3]) + (" …" if total[j] > 3 else ""))
            if selecting:
                body.append(f"{sel[j]} of them highlighted")
            bars.append(dict(
                y=((axis.edges[j] + axis.edges[j + 1]) / 2 - lo) / (hi - lo),
                len=round(total[j] / biggest, 4), sel=round(sel[j] / biggest, 4),
                chosen=j in chosen, bin=j, title=f"{axis.label}: {axis.bin_label(j)}", body=body,
                hint="Click to remove this filter" if j in chosen else "Click to highlight these teams",
            ))
        ticks = [[(e - lo) / (hi - lo), axis.edge(e)] for e in axis.edges[lo_j:hi_j + 1]]
        axes.append(dict(key=axis.key, label=axis.label, ticks=ticks, bars=bars))
    return axes, np.column_stack(ys)


def build(df: pd.DataFrame, league: str | None = None) -> tuple[dict, pd.DataFrame, np.ndarray]:
    """Component data, the team table, and which teams are highlighted."""
    if league:
        df = df[df['league_name'] == league]
    teams = team_profiles(df)
    where = league or "all leagues"
    payload = dict(title=f"📈 4. Team profiles · {len(teams)} teams · {where}", n=len(teams), k=len(AXES),
                   colors=dict(highlight=COLOR_PALETTE['highlight'], neutral=COLOR_PALETTE['neutral']),
                   pins=interaction.pinned_teams())
    if teams.empty:
        return payload | dict(axes=[dict(key=a.key, label=a.label, ticks=[], bars=[]) for a in AXES],
                              teams=[]), teams, np.zeros(0, bool)

    selecting = bool(chosen_bins())
    picked = highlight_mask(teams)
    axes, y = _axes_payload(teams, picked, selecting)
    n_picked = int(picked.sum())

    # Worst team = full blue, average team = middle, best team = full red.
    ppg = teams['ppg']
    lo, avg, hi = ppg.min(), ppg.mean(), ppg.max()
    norm = np.where(ppg < avg, 0.5 * (ppg - lo) / max(avg - lo, 1e-9),
                    0.5 + 0.5 * (ppg - avg) / max(hi - avg, 1e-9)).clip(0, 1).tolist()
    txt = np.array([[a.fmt(v) for a, v in zip(AXES, row)] for row in teams[[a.key for a in AXES]].to_numpy()])
    return payload | dict(
        axes=axes,
        ys=np.round(y.ravel(), 4).tolist(),
        txt=txt.ravel().tolist(),
        teams=teams.index.tolist(),
        sub=[f"{lg} · {m} matches · {p:.2f} points / game"
             for lg, m, p in zip(teams['league_name'], teams['matches'], ppg)],
        colorLight=sample_colorscale(PPG_COLORSCALE_LIGHT, norm),
        colorDark=sample_colorscale(PPG_COLORSCALE_DARK, norm),
        hl=picked.astype(int).tolist() if selecting else None,
        lineAlpha=float(np.clip(5 / np.sqrt(max(n_picked, 1)), 0.4, 0.95)) if selecting else 0.7,
        lineWidth=2.2 if selecting and n_picked <= 15 else 1.4,
        legend=dict(label=f"Points / game (middle = average, {avg:.2f})",
                    lo=f"{lo:.2f}", hi=f"{hi:.2f}",
                    stopsLight=[c for _, c in PPG_COLORSCALE_LIGHT],
                    stopsDark=[c for _, c in PPG_COLORSCALE_DARK]),
    ), teams, picked


# ── Page ─────────────────────────────────────────────────────────────────────────────────────

def _read_click():
    """The component reports each click as state value 'click' = {cd: [kind, id, ...], nonce}."""
    value = st.session_state.get(CHART_KEY)
    try:
        click = value['click']
    except (KeyError, TypeError):
        click = getattr(value, 'click', None)
    return click if isinstance(click, dict) else None


def _handle(cd) -> bool:
    if not isinstance(cd, (list, tuple)) or not cd:
        return False
    if cd[0] == 'pin':
        interaction.toggle_team(cd[1])
    elif cd[0] == 'bin' and cd[1] in AXIS_BY_KEY:
        toggle_bin(cd[1], int(cd[2]))
    else:
        return False
    return True


def _apply_click() -> bool:
    """Apply a click once (the callback and the fallback in render() share the nonce bookkeeping)."""
    click = _read_click()
    if not click or click.get('nonce') == st.session_state.get("pc_last_nonce"):
        return False
    st.session_state["pc_last_nonce"] = click.get('nonce')
    return _handle(click.get('cd'))


def _status_bar():
    chips = [(f"{AXIS_BY_KEY[k].label}: {', '.join(AXIS_BY_KEY[k].bin_label(j) for j in js)}", clear_bins, (k,))
             for k, js in chosen_bins().items()]
    chips += [(f"📌 {t}", interaction.toggle_team, (t,)) for t in interaction.pinned_teams()]
    if not chips:
        st.caption("👆 **Hover a line** to see the team, **click it** to pin it (it is pinned in chart 5 too). "
                   "**Click a bar** on an axis to highlight the teams in that range.")
        return
    with st.container(horizontal=True, vertical_alignment="center", gap="small"):
        for i, (label, callback, args) in enumerate(chips):
            st.button(f"✕ {label}", key=f"pc_chip_{i}", on_click=callback, args=args, help="Remove")
        if len(chips) > 1:
            st.button("Clear all", key="pc_clear_all", type="tertiary",
                      on_click=lambda: (clear_bins(), interaction.clear_teams()))


def _table(teams: pd.DataFrame):
    cols = {'league_name': 'League', 'matches': 'Matches'} | {a.key: a.label for a in AXES}
    st.dataframe(
        teams.sort_values('ppg', ascending=False)[list(cols)].rename(columns=cols),
        width="stretch",
        column_config={a.label: st.column_config.NumberColumn(format="%.0f%%" if a.pct else "%.2f")
                       for a in AXES},
    )


def render(df: pd.DataFrame):
    leagues = sorted(df['league_name'].unique())
    league = st.pills("League", leagues, key="parallel_coordinates_league",
                      on_change=clear_bins, help="Click a league to show only its teams; click it again for all.")
    _status_bar()

    data, teams, picked = build(df, league)
    result = _COMPONENT(key=CHART_KEY, data=data, on_click_change=_apply_click, height="content")
    # Fallback: if the callback didn't see the click, apply it now and redraw.
    click = getattr(result, 'click', None)
    if isinstance(click, dict) and click.get('nonce') != st.session_state.get("pc_last_nonce"):
        st.session_state["pc_last_nonce"] = click.get('nonce')
        if _handle(click.get('cd')):
            st.rerun()

    if teams.empty:
        st.info(f"No team has {MIN_MATCHES}+ matches in the current filter. Broaden the sidebar filters.")
        return

    pinned = teams[teams.index.isin(interaction.pinned_teams())]
    if len(pinned):
        st.markdown("##### 📌 Pinned teams")
        _table(pinned)
    if chosen_bins():
        st.markdown(f"##### 🟩 Highlighted teams · {int(picked.sum())} of {len(teams)}")
        _table(teams[picked])
    with st.expander(f"🔍 All {len(teams)} teams"):
        _table(teams)
    st.caption(f"Teams with fewer than {MIN_MATCHES} matches in the current filter are left out.")
