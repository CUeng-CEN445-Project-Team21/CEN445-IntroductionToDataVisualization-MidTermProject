"""
theme.py - Shared look for every chart and ML figure. Change it here, not in individual charts.
The page itself (background, sidebar, fonts) is themed in .streamlit/config.toml.
"""

# None = no fixed Plotly template. st.plotly_chart then applies Streamlit's own theme,
# which follows the visitor's light/dark setting. Avoid hard-coding background or
# text colours in charts for the same reason; use colours that read on both.
THEME_TEMPLATE = None

# Match outcomes. Checked for colour-blind separation and contrast on both the light
# (#F3EFE4) and dark (#0F1813) page background. Draw is lighter, so text or labels
# printed inside a draw segment should use dark ink.
COLOR_PALETTE = {
    'home': '#1C7AAE',       # petrol blue
    'draw': '#C08A12',       # ochre
    'away': '#C23A5E',       # raspberry
    'neutral': '#8A8476',    # warm grey (chalk on turf)
    'highlight': '#C08A12',  # ochre, same accent as the page header
}

# For "above / below expectation" encodings (e.g. bookmaker under- vs over-pricing).
# A diverging pair with a grey midpoint; also checked for colour-blind separation.
DIVERGING = {
    'positive': '#008C84',   # teal
    'negative': '#D2602A',   # burnt orange
    'neutral': COLOR_PALETTE['neutral'],
}

# Recessive lines (reference lines, outlines, connectors) that read on both themes.
GUIDE_LINE = 'rgba(138, 132, 118, 0.65)'


def rgba(hex_color: str, alpha: float) -> str:
    """'#1C7AAE', 0.4 -> 'rgba(28, 122, 174, 0.4)'"""
    h = hex_color.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


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
