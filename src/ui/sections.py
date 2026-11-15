"""
sections.py - Page header with KPI row, and the data explorer / footer at the bottom.
"""

import pandas as pd
import streamlit as st


def header(df: pd.DataFrame):
    st.markdown(
        '<div class="mast">'
        '<div class="mast-eyebrow">CEN445 · Introduction to Data Visualization · Team 21</div>'
        '<div class="mast-title">European Football <span class="thin">Intelligence &amp;</span> Match Dynamics</div>'
        '<div class="mast-sub">Results, goals and betting markets across Europe\'s top leagues. '
        'Every chart and model on this page follows the filters in the sidebar.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    total = len(df)
    avg_goals = df['total_goals'].mean() if total else 0
    home_win_rate = (df['ftr'] == 'H').mean() * 100 if total else 0
    over_25_rate = (df['is_over_25'] == 1).mean() * 100 if total else 0
    btts_rate = (df['btts'] == 1).mean() * 100 if total else 0

    kpi1.metric("Matches Displayed", f"{total:,}", border=True)
    kpi2.metric("Avg Goals / Match", f"{avg_goals:.2f}", border=True)
    kpi3.metric("Home Win Advantage", f"{home_win_rate:.1f}%", border=True)
    kpi4.metric("Over 2.5 Goals", f"{over_25_rate:.1f}%", border=True)
    kpi5.metric("Both Teams Scored", f"{btts_rate:.1f}%", border=True)


def data_explorer(df: pd.DataFrame):
    st.write("---")
    with st.expander("Explore the filtered data & export", icon=":material/table_view:"):
        st.dataframe(df.head(100), width="stretch")
        st.download_button(
            label="Download filtered data as CSV",
            icon=":material/download:",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name="filtered_matches_cen445.csv",
            mime="text/csv"
        )


def footer():
    st.markdown(
        '<div class="foot"><span>CEN445 Introduction to Data Visualization · Team 21</span>'
        '<span>Python · Streamlit · Plotly · scikit-learn</span></div>',
        unsafe_allow_html=True,
    )
