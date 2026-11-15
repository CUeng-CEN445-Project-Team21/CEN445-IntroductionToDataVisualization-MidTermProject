"""
theme.py - Shared look for every chart and ML figure. Change it here, not in individual charts.
"""

# None = no fixed Plotly template. st.plotly_chart then applies Streamlit's own theme,
# which follows the visitor's light/dark setting. Avoid hard-coding background or
# text colours in charts for the same reason; use colours that read on both.
THEME_TEMPLATE = None

COLOR_PALETTE = {
    'home': '#3B82F6',       # Blue
    'draw': '#F59E0B',       # Amber
    'away': '#EF4444',       # Red
    'neutral': '#64748B',    # Slate
    'highlight': '#10B981',  # Emerald
}

# Result colours keyed the way the dataset stores them
RESULT_COLORS = {'Home Win': COLOR_PALETTE['home'], 'Draw': COLOR_PALETTE['draw'], 'Away Win': COLOR_PALETTE['away']}

# One fixed colour per league, so a league keeps its colour whatever the sidebar filter shows.
# Eight categorical hues in a CVD-checked order; charts that use them also label each league directly.
LEAGUE_COLORS = {
    'Bundesliga':     '#2a78d6',  # blue
    'Eredivisie':     '#eb6834',  # orange
    'La Liga':        '#1baf7a',  # aqua
    'Ligue 1':        '#eda100',  # yellow
    'Premier League': '#e87ba4',  # magenta
    'Primeira Liga':  '#008300',  # green
    'Serie A':        '#6250d6',  # violet
    'Süper Lig':      '#e34948',  # red
}
