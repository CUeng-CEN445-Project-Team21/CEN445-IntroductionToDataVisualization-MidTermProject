"""
9. ANALYTICAL: League Goal Distribution (Violin & Box Plot with Outliers)
Insight: Detects variance, goal inflation and extreme high-scoring outliers.
Includes dynamic goal-based league sorting, benchmark threshold lines (2.5 & 3.5 goals),
and enriched outlier match inspection.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.theme import THEME_TEMPLATE


def build(
    df: pd.DataFrame,
    sort_order: str = "Goal Output (High to Low)",
    benchmark_line: str = "2.5 Goals (Standard Over/Under)"
) -> go.Figure:
    plot_df = df.copy()

    # Determine sorting order
    if sort_order == "Goal Output (High to Low)":
        league_ranking = (
            plot_df.groupby('league_name')['total_goals']
            .mean()
            .sort_values(ascending=False)
            .index.tolist()
        )
    else:
        league_ranking = sorted(plot_df['league_name'].unique().tolist())

    # Format date for cleaner hover display
    if 'match_date' in plot_df.columns:
        plot_df['formatted_date'] = pd.to_datetime(plot_df['match_date'], errors='coerce').dt.strftime('%b %d, %Y')
    else:
        plot_df['formatted_date'] = ""

    # Generate custom hover text for individual match outliers
    plot_df['hover_match_info'] = (
        "<b>" + plot_df['home_team'] + " " +
        plot_df['fthg'].astype(str) + " - " + plot_df['ftag'].astype(str) + " " +
        plot_df['away_team'] + "</b><br>" +
        "League: " + plot_df['league_name'] + "<br>" +
        "Date: " + plot_df['formatted_date'] + "<br>" +
        "Total Goals: <b>" + plot_df['total_goals'].astype(str) + "</b>"
    )

    fig = px.violin(
        plot_df,
        x='league_name',
        y='total_goals',
        color='league_name',
        category_orders={'league_name': league_ranking},
        box=True,
        points='outliers',
        hover_name='hover_match_info',
        title="9. League Total Goal Distributions & Outlier Matches"
    )

    # Clean up traces: remove hover from violin density, keep only box and outlier hovers
    fig.update_traces(
        meanline_visible=True,
        box_line_width=1.5
    )

    # Benchmark Threshold Line
    threshold_val = None
    if benchmark_line == "2.5 Goals (Standard Over/Under)":
        threshold_val = 2.5
    elif benchmark_line == "3.5 Goals (High-Scoring Threshold)":
        threshold_val = 3.5

    if threshold_val is not None:
        fig.add_hline(
            y=threshold_val,
            line_dash="dash",
            line_color="#EF4444",
            line_width=2,
            annotation_text=f"Benchmark: {threshold_val} Goals",
            annotation_position="top right",
            annotation_font=dict(color="#EF4444", size=11)
        )

    # Compute league averages for subtitle / annotation
    top_league = league_ranking[0]
    bot_league = league_ranking[-1]
    top_avg = plot_df[plot_df['league_name'] == top_league]['total_goals'].mean()
    bot_avg = plot_df[plot_df['league_name'] == bot_league]['total_goals'].mean()

    fig.add_annotation(
        text=f"Highest Output: <b>{top_league}</b> ({top_avg:.2f} g/m) &nbsp;|&nbsp; Tightest Defense: <b>{bot_league}</b> ({bot_avg:.2f} g/m)",
        xref="paper", yref="paper",
        x=0.01, y=1.04,
        showarrow=False,
        font=dict(size=11, color="#94A3B8")
    )

    fig.update_layout(
        template=THEME_TEMPLATE,
        showlegend=False,
        xaxis_title="European League (Ranked)",
        yaxis_title="Total Match Goals (FT)",
        height=450,
        margin=dict(l=10, r=10, t=55, b=10)
    )
    return fig


def render(df: pd.DataFrame):
    c1, c2 = st.columns([1, 1])
    with c1:
        sort_order = st.pills(
            "Sort Order",
            options=["Goal Output (High to Low)", "Alphabetical"],
            default="Goal Output (High to Low)",
            key="violin_sort_order"
        )
    with c2:
        benchmark_line = st.selectbox(
            "Benchmark Line",
            options=["2.5 Goals (Standard Over/Under)", "3.5 Goals (High-Scoring Threshold)", "None"],
            key="violin_benchmark_line"
        )

    selected_sort = sort_order if sort_order else "Goal Output (High to Low)"
    st.plotly_chart(build(df, sort_order=selected_sort, benchmark_line=benchmark_line), width="stretch")
