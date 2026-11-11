"""
sections.py - Page header with KPI row, and the data explorer / footer at the bottom.
"""

import pandas as pd
import streamlit as st


def header(df: pd.DataFrame):
    st.markdown('<div class="main-header">European Football Intelligence & Match Dynamics</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Interactive Exploratory Visualization Dashboard • CEN445 Assignment</div>',
                unsafe_allow_html=True)

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    total = len(df)
    avg_goals = df['total_goals'].mean() if total else 0
    home_win_rate = (df['ftr'] == 'H').mean() * 100 if total else 0
    over_25_rate = (df['is_over_25'] == 1).mean() * 100 if total else 0
    btts_rate = (df['btts'] == 1).mean() * 100 if total else 0

    kpi1.metric("Matches Displayed", f"{total:,}")
    kpi2.metric("Avg Goals / Match", f"{avg_goals:.2f}")
    kpi3.metric("Home Win Advantage", f"{home_win_rate:.1f}%")
    kpi4.metric("Over 2.5 Goals", f"{over_25_rate:.1f}%")
    kpi5.metric("Both Teams Scored", f"{btts_rate:.1f}%")

    st.write("---")


def data_explorer(df: pd.DataFrame):
    st.write("---")
    with st.expander("📥 Explore Filtered Data & Export"):
        st.dataframe(df.head(100), width="stretch")
        st.download_button(
            label="⬇️ Download Filtered Data as CSV",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name="filtered_matches_cen445.csv",
            mime="text/csv"
        )


def footer():
    st.caption("CEN445 Introduction to Data Visualization • Team Project Dashboard • Built with Python & Streamlit")
