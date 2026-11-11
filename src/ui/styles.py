"""
styles.py - Custom CSS for the HTML elements in the header. Chart styling lives in src/theme.py.
"""

import streamlit as st

CSS = """
<style>
    /* Colours here must work on both the light and dark theme. */
    .main-header {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #0EA5E9 0%, #6366F1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .sub-header {
        opacity: 0.7;              /* muted version of the theme's own text colour */
        font-size: 1.05rem;
        margin-bottom: 1.2rem;
    }
</style>
"""


def apply():
    st.markdown(CSS, unsafe_allow_html=True)
