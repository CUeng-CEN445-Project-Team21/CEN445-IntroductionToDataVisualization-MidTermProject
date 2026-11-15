"""
linked.py - One shared click-selection for charts 4, 5 and 6 (not a chart itself).

Clicking something in one of these charts adds a filter here, and all three charts then
highlight the matches that pass every active filter:

  * Chart 4 (parallel coordinates): click a bar on an axis -> matches in that bin.
    Bars on the same axis are OR-ed, bars on different axes AND-ed (like brushing).
  * Chart 5 (network): click a team -> its matches; click an arrow -> that head-to-head.
  * Chart 6 (odds contour): click an area -> matches in that home/away odds cell.

Pins are separate from filters: clicking a single strand in chart 4 (or a match dot in chart 6)
pins that match. Pinned matches stay drawn bold in chart 4 and ringed in chart 6, whatever
the filters are, so they can be followed across axes. They never narrow the selection.

Clicking the same thing again removes it. Streamlit resets a chart's own selection every time
its figure changes, so clicks are copied into st.session_state[STATE] by a callback and kept there.

Every click arrives as a list [kind, id, ...]; kind is one of "team", "pair", "bin", "cell", "pin".
Plotly charts carry it as the point's customdata; chart 4's custom component sends it directly.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
import streamlit as st

STATE = "linked_selection"


# ── Bins (shared so a click in one chart means the same thing in the others) ─────────────────

@dataclass(frozen=True)
class Axis:
    key: str            # dataframe column
    label: str
    edges: tuple = ()   # odds axes: bin edges; a value's position inside its bin is log-interpolated
    slots: tuple = ()   # discrete axes: one label per slot

    @property
    def n(self) -> int:
        return len(self.slots) if self.slots else len(self.edges) - 1

    def bin_label(self, i: int) -> str:
        if self.slots:
            return self.slots[i]
        if i == 0:
            return f"< {self.edges[1]:g}"
        if i == self.n - 1:
            return f"≥ {self.edges[-2]:g}"
        return f"{self.edges[i]:g}–{self.edges[i + 1]:g}"


ODDS_1X2 = (1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0, 5.0, 7.0, 10.0, 40.0)
AXES = (
    Axis('home_odds', 'Home odds', edges=ODDS_1X2),
    Axis('away_odds', 'Away odds', edges=ODDS_1X2),
    Axis('draw_odds', 'Draw odds', edges=(2.0, 3.0, 3.25, 3.5, 3.75, 4.0, 4.5, 5.0, 6.0, 8.0, 17.0)),
    Axis('over_25_odds', 'Over 2.5 odds', edges=(1.0, 1.3, 1.45, 1.6, 1.75, 1.9, 2.05, 2.25, 2.6, 3.5)),
    Axis('total_goals', 'Total goals', slots=('0', '1', '2', '3', '4', '5', '6', '7+')),
    Axis('ftr', 'Result', slots=('Home win', 'Draw', 'Away win')),
)
AXIS_BY_KEY = {a.key: a for a in AXES}
RESULT_SLOT = {'H': 0, 'D': 1, 'A': 2}

# Clickable cells of the odds contour (home odds x away odds), equal width on a log scale.
CELL_EDGES = tuple(np.round(np.geomspace(1.0, 40.0, 21), 2))
N_CELLS = len(CELL_EDGES) - 1


def axis_bins(axis: Axis, df: pd.DataFrame) -> np.ndarray:
    """Bin index (0 .. axis.n-1) of every row on this axis."""
    if axis.key == 'ftr':
        return df['ftr'].map(RESULT_SLOT).to_numpy(dtype=int)
    if axis.key == 'total_goals':
        return np.clip(df['total_goals'].to_numpy(dtype=int), 0, axis.n - 1)
    idx = np.searchsorted(axis.edges, df[axis.key].to_numpy(dtype=float), side='right') - 1
    return np.clip(idx, 0, axis.n - 1)


def cell_index(odds) -> np.ndarray:
    idx = np.searchsorted(CELL_EDGES, np.asarray(odds, dtype=float), side='right') - 1
    return np.clip(idx, 0, N_CELLS - 1)


def cell_label(i: int, j: int) -> str:
    return (f"home odds {CELL_EDGES[i]:g}–{CELL_EDGES[i + 1]:g}, "
            f"away odds {CELL_EDGES[j]:g}–{CELL_EDGES[j + 1]:g}")


# ── State ────────────────────────────────────────────────────────────────────────────────────

def state() -> dict:
    s = st.session_state.setdefault(STATE, {})
    # setdefault per key, so a session that started on an older version of this file keeps working
    for key, default in (('team', None), ('pair', None), ('bins', {}), ('cell', None), ('pins', [])):
        s.setdefault(key, default)
    return s


def active() -> bool:
    """True when any filter is set (pins don't count: they never filter)."""
    s = state()
    return bool(s['team'] or s['pair'] or s['bins'] or s['cell'])


def pins() -> list:
    return state()['pins']


def mask(df: pd.DataFrame) -> pd.Series:
    """True for every match that passes all active click filters (all True if none)."""
    s = state()
    m = pd.Series(True, index=df.index)
    if s['team']:
        m &= (df['home_team'] == s['team']) | (df['away_team'] == s['team'])
    if s['pair']:
        a, b = s['pair']
        m &= ((df['home_team'] == a) & (df['away_team'] == b)) | \
             ((df['home_team'] == b) & (df['away_team'] == a))
    for key, chosen in s['bins'].items():
        m &= np.isin(axis_bins(AXIS_BY_KEY[key], df), list(chosen))
    if s['cell']:
        i, j = s['cell']
        m &= (cell_index(df['home_odds']) == i) & (cell_index(df['away_odds']) == j)
    return m


def toggle_team(team: str):
    s = state()
    s['team'] = None if s['team'] == team else team
    s['pair'] = None


def toggle_pair(a: str, b: str):
    s = state()
    pair = tuple(sorted((a, b)))
    s['pair'] = None if s['pair'] == pair else pair
    s['team'] = None


def toggle_bin(axis_key: str, i: int):
    s = state()
    chosen = set(s['bins'].get(axis_key, ()))
    chosen ^= {i}
    if chosen:
        s['bins'][axis_key] = sorted(chosen)
    else:
        s['bins'].pop(axis_key, None)


def toggle_cell(i: int, j: int):
    s = state()
    s['cell'] = None if s['cell'] == (i, j) else (i, j)


def toggle_pin(match_id: int):
    s = state()
    s['pins'] = [p for p in s['pins'] if p != match_id] if match_id in s['pins'] else s['pins'] + [match_id]


def clear(*parts: str):
    """Clear the named parts ('team', 'pair', 'bins', 'cell', 'pins'), or every filter and pin."""
    s = state()
    for part in parts or ('team', 'pair', 'bins', 'cell', 'pins'):
        s[part] = {} if part == 'bins' else [] if part == 'pins' else None


def _clear_axis(axis_key: str):
    state()['bins'].pop(axis_key, None)


# ── Click handling ───────────────────────────────────────────────────────────────────────────

def handle(cd) -> bool:
    """Apply one click, given as [kind, id, ...]. Returns False if it wasn't a known click."""
    if not isinstance(cd, (list, tuple)) or not cd:
        return False
    kind = cd[0]
    if kind == 'team':
        toggle_team(cd[1])
    elif kind == 'pair':
        toggle_pair(cd[1], cd[2])
    elif kind == 'bin':
        toggle_bin(cd[1], int(cd[2]))
    elif kind == 'cell':
        toggle_cell(int(cd[1]), int(cd[2]))
    elif kind == 'pin':
        toggle_pin(int(cd[1]))
    else:
        return False
    return True


def on_click(chart_key: str):
    """on_select callback for st.plotly_chart(..., key=chart_key, selection_mode="points")."""
    def _callback():
        try:
            points = st.session_state[chart_key]['selection']['points']
        except (KeyError, TypeError):
            return
        if points:                  # empty = double-click / deselect: nothing to do
            handle(points[-1].get('customdata'))
    return _callback


def plotly_chart(fig, key: str):
    """st.plotly_chart wired to the shared selection."""
    st.plotly_chart(fig, width="stretch", key=key, on_select=on_click(key), selection_mode="points",
                    config={'displaylogo': False})


# ── Status bar ───────────────────────────────────────────────────────────────────────────────

def _chips(df: pd.DataFrame) -> list:
    """(label, callback, args) for every active filter."""
    s, chips = state(), []
    if s['team']:
        chips.append((f"Team: {s['team']}", clear, ('team',)))
    if s['pair']:
        chips.append((f"Head-to-head: {s['pair'][0]} vs {s['pair'][1]}", clear, ('pair',)))
    for key, chosen in s['bins'].items():
        axis = AXIS_BY_KEY[key]
        chips.append((f"{axis.label}: {', '.join(axis.bin_label(i) for i in chosen)}", _clear_axis, (key,)))
    if s['cell']:
        chips.append((f"Area: {cell_label(*s['cell'])}", clear, ('cell',)))
    if len(s['pins']) > 3:
        chips.append((f"📌 {len(s['pins'])} pinned matches", clear, ('pins',)))
    else:
        for match_id in s['pins']:
            chips.append((f"📌 {match_label(df, match_id)}", toggle_pin, (match_id,)))
    return chips


def match_label(df: pd.DataFrame, match_id: int) -> str:
    row = df[df['id'] == match_id]
    if row.empty:
        return f"match {match_id} (filtered out)"
    r = row.iloc[0]
    return f"{r['home_team']} {r['fthg']}–{r['ftag']} {r['away_team']}"


def status_bar(df: pd.DataFrame):
    chips = _chips(df)
    if not chips:
        st.caption("👆 **Everything here is clickable.** Hover a strand to follow it, click it to pin it. "
                   "Click a bar on an axis, a team or an arrow in the network, or an area of the odds map — "
                   "charts 4–6 all highlight the related matches. Click the same thing again to remove it.")
        return
    with st.container(horizontal=True, vertical_alignment="center", gap="small"):
        if active():
            st.markdown(f"🔗 **{int(mask(df).sum()):,} matches highlighted** in charts 4–6")
        for i, (label, callback, args) in enumerate(chips):
            st.button(f"✕ {label}", key=f"linked_chip_{i}", on_click=callback, args=args,
                      help="Remove this filter")
        if len(chips) > 1:
            st.button("Clear all", key="linked_clear_all", on_click=clear, type="tertiary")
