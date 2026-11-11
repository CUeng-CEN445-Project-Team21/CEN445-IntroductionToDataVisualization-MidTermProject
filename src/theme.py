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
