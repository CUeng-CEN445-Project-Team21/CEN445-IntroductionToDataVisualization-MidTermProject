"""
loader.py - Loads the processed dataset for the app, rebuilding it first if data/raw/ changed.
"""

import pandas as pd
import streamlit as st

from src.data import pipeline


def _raw_fingerprint() -> tuple:
    """Cheap snapshot of data/raw/ (names, sizes, mtimes). Changes whenever a file is added or edited."""
    return tuple(
        (p.name, p.stat().st_size, p.stat().st_mtime_ns)
        for p in sorted(pipeline.RAW_DIR.iterdir()) if p.is_file()
    )


@st.cache_data(show_spinner="Loading match data...")
def _load(fingerprint: tuple) -> pd.DataFrame:
    if pipeline.is_stale():
        try:
            with st.spinner("New data detected in data/raw/ — rebuilding dataset..."):
                df, report = pipeline.build()
            for warning in report.warnings:
                st.warning(warning)
            return df
        except Exception as e:
            if not pipeline.PARQUET_PATH.exists():
                st.error(f"Could not build the dataset: {e}")
                return pd.DataFrame()
            st.warning(f"Rebuilding the dataset failed, showing the last saved version instead. ({e})")
    return pd.read_parquet(pipeline.PARQUET_PATH)


def load_data() -> pd.DataFrame:
    pipeline.RAW_DIR.mkdir(parents=True, exist_ok=True)
    return _load(_raw_fingerprint())
