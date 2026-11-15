"""
interaction.py - Click handling shared by charts 4-6 (not a chart itself).

* Pinned teams are shared by charts 4 and 5: click a team's line in the parallel coordinates
  or a team in the network, and it is pinned in both. Click it again to unpin.
* plotly_chart() turns a click on a Plotly point into one call of on_click(customdata).

Streamlit resets a chart's own selection whenever its figure changes, so every click is
copied into st.session_state by a callback and kept there.
"""

import streamlit as st

PINS = "pinned_teams"


def pinned_teams() -> list:
    return st.session_state.setdefault(PINS, [])


def toggle_team(team: str):
    pins = pinned_teams()
    st.session_state[PINS] = [t for t in pins if t != team] if team in pins else pins + [team]


def clear_teams():
    st.session_state[PINS] = []


def plotly_chart(fig, key: str, on_click):
    """st.plotly_chart where clicking a point calls on_click(that point's customdata)."""
    def _callback():
        try:
            points = st.session_state[key]['selection']['points']
        except (KeyError, TypeError):
            return
        if points:                  # empty = double-click / deselect: nothing to do
            on_click(points[-1].get('customdata'))

    st.plotly_chart(fig, width="stretch", key=key, on_select=_callback, selection_mode="points",
                    config={'displaylogo': False})
