"""
app.py - Entry point. Run with:  streamlit run app.py

This file only wires the page together. To change:
  * filters ................ src/ui/sidebar.py
  * header, KPIs, footer ... src/ui/sections.py
  * which chart goes where . src/ui/layout.py
  * a chart ................ src/charts/<chart>.py
  * chart colours/theme .... src/theme.py
  * the dataset ............ drop files in data/raw/ (see src/data/pipeline.py)
"""

import os
import sys

import streamlit as st

# Ensure src modules are resolvable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data.loader import load_data
from src.ui import layout, sections, sidebar, styles

st.set_page_config(
    page_title="European Football Intelligence | CEN445",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)
styles.apply()

df_raw = load_data()
if df_raw.empty:
    st.stop()

df = sidebar.render(df_raw)

sections.header(df)
if df.empty:
    st.warning("No matches fit these filters. Broaden your selections in the sidebar.",
               icon=":material/filter_alt_off:")
    st.stop()

layout.render(df)

sections.data_explorer(df)
sections.footer()
