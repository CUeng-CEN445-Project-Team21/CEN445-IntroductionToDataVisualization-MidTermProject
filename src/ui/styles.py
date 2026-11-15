"""
styles.py - Custom CSS on top of the Streamlit theme (.streamlit/config.toml).
Chart colours live in src/theme.py.

The same CSS serves the light and dark theme, so it never hard-codes a text or
background colour: it works from `currentColor` (the theme's text colour) and
transparency. The one fixed colour is ACCENT, which reads on both backgrounds.
"""

import streamlit as st

ACCENT = "#C08A12"  # ochre: the stripe on the masthead and section labels

CSS = f"""
<style>
    /* ---- Masthead ---------------------------------------------------------- */
    .mast {{
        position: relative;
        padding: 0.4rem 0 1.1rem 0;
        margin-bottom: 1.1rem;
    }}
    /* mown-pitch stripes along the bottom edge */
    .mast::after {{
        content: "";
        position: absolute;
        left: 0; right: 0; bottom: 0;
        height: 6px;
        background: repeating-linear-gradient(90deg,
            currentColor 0 48px, transparent 48px 96px);
        opacity: 0.14;
    }}
    .mast-eyebrow {{
        font-family: "Barlow Condensed", sans-serif;
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        opacity: 0.65;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }}
    .mast-eyebrow::before {{
        content: "";
        width: 28px; height: 3px;
        background: {ACCENT};
    }}
    .mast-title {{
        font-family: "Barlow Condensed", sans-serif;
        font-weight: 800;
        font-size: clamp(2rem, 4.2vw, 3.2rem);
        line-height: 1.0;
        letter-spacing: -0.01em;
        text-transform: uppercase;
        margin: 0.35rem 0 0.5rem 0;
    }}
    .mast-title .thin {{
        font-weight: 500;
        opacity: 0.55;
    }}
    .mast-sub {{
        max-width: 60rem;
        font-size: 1.02rem;
        opacity: 0.72;
    }}

    /* ---- Section label above each chart group ------------------------------ */
    .section-kicker {{
        font-family: "Barlow Condensed", sans-serif;
        font-weight: 700;
        font-size: 0.8rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: {ACCENT};
        margin-top: 0.6rem;
    }}

    /* ---- KPI tiles: scoreboard numbers ------------------------------------- */
    [data-testid="stMetric"] {{
        border-top: 3px solid {ACCENT} !important;
    }}
    [data-testid="stMetricLabel"] p {{
        font-family: "Barlow Condensed", sans-serif;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        font-size: 0.8rem;
        opacity: 0.75;
    }}
    [data-testid="stMetricValue"] {{
        font-family: "Barlow Condensed", sans-serif;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
    }}

    /* ---- Tabs: condensed, uppercase ---------------------------------------- */
    [data-baseweb="tab"] p {{
        font-family: "Barlow Condensed", sans-serif;
        font-weight: 700;
        font-size: 1.05rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }}

    /* ---- Sidebar group labels ---------------------------------------------- */
    .side-label {{
        font-family: "Barlow Condensed", sans-serif;
        font-weight: 700;
        font-size: 0.78rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        opacity: 0.6;
        margin: 1.1rem 0 0.3rem 0;
        padding-bottom: 0.25rem;
        border-bottom: 1px solid color-mix(in srgb, currentColor 22%, transparent);
    }}

    /* ---- Footer ------------------------------------------------------------- */
    .foot {{
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        gap: 0.5rem;
        font-size: 0.85rem;
        opacity: 0.6;
        padding-top: 0.6rem;
    }}
</style>
"""


def apply():
    st.markdown(CSS, unsafe_allow_html=True)
