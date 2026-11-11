"""
pipeline.py - Turns every file in data/raw/ into data/processed/matches.parquet.

Supported inputs (format is detected from the columns, not the file name):
  * football-data.co.uk files (.csv / .xlsx, one league or the all-leagues workbook)
  * SQLite databases (.db / .sqlite) with a table using the base column names
  * Already-processed files (.csv / .parquet) using the base column names (see schema.py)

Steps: read -> normalise to base columns -> validate -> merge & de-duplicate -> enrich -> save.

The app runs this automatically when data/raw/ changes. To run it by hand:
    python -m src.data.pipeline
"""

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.schema import (
    BASE_COLUMNS, LEAGUE_METADATA, MATCH_KEY, OUTPUT_COLUMNS, REQUIRED_COLUMNS,
)

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
PARQUET_PATH = PROCESSED_DIR / "matches.parquet"
MANIFEST_PATH = PROCESSED_DIR / "manifest.json"

TABLE_EXTS = {".csv", ".parquet", ".xlsx", ".xls"}
SQLITE_EXTS = {".db", ".sqlite", ".sqlite3"}
IGNORED_EXTS = {".md", ".txt", ".gitkeep"}

# football-data.co.uk column -> base column
FOOTBALL_DATA_RENAME = {
    'Div': 'division', 'Date': 'match_date', 'HomeTeam': 'home_team', 'AwayTeam': 'away_team',
    'FTHG': 'fthg', 'FTAG': 'ftag', 'FTR': 'ftr', 'HTHG': 'hthg', 'HTAG': 'htag', 'HTR': 'htr',
}
# Odds columns in order of preference (market average first, then single bookmakers).
FOOTBALL_DATA_ODDS = {
    'home_odds':     ['AvgH', 'B365H', 'PSH', 'BbAvH', 'WHH', 'MaxH'],
    'draw_odds':     ['AvgD', 'B365D', 'PSD', 'BbAvD', 'WHD', 'MaxD'],
    'away_odds':     ['AvgA', 'B365A', 'PSA', 'BbAvA', 'WHA', 'MaxA'],
    'over_25_odds':  ['Avg>2.5', 'B365>2.5', 'P>2.5', 'BbAv>2.5', 'Max>2.5'],
    'under_25_odds': ['Avg<2.5', 'B365<2.5', 'P<2.5', 'BbAv<2.5', 'Max<2.5'],
}

RESULT_LABELS = {'H': 'Home Win', 'D': 'Draw', 'A': 'Away Win'}


@dataclass
class BuildReport:
    rows: int = 0
    files: dict = field(default_factory=dict)      # file name -> valid rows read
    warnings: list = field(default_factory=list)


# ------------------------------------------------------------------------------
# 1. Reading & normalising
# ------------------------------------------------------------------------------
def _season_from_date(dates: pd.Series) -> pd.Series:
    """European seasons run Aug-May: 2024-03-10 -> '2023-2024'."""
    start = np.where(dates.dt.month >= 7, dates.dt.year, dates.dt.year - 1)
    return pd.Series([f"{y}-{y + 1}" for y in start], index=dates.index)


def _first_available(df: pd.DataFrame, candidates: list) -> pd.Series:
    present = [c for c in candidates if c in df.columns]
    if not present:
        return pd.Series(np.nan, index=df.index)
    values = df[present].apply(pd.to_numeric, errors='coerce')
    return values.bfill(axis=1).iloc[:, 0]


def _normalise(df: pd.DataFrame):
    """Converts one table to base columns. Returns None if the format is not recognised."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    if {'FTHG', 'HomeTeam', 'Div'}.issubset(df.columns):          # football-data.co.uk
        out = df.rename(columns=FOOTBALL_DATA_RENAME)
        for target, candidates in FOOTBALL_DATA_ODDS.items():
            out[target] = _first_available(df, candidates)
        # football-data uses dd/mm/yyyy, older files dd/mm/yy
        out['match_date'] = pd.to_datetime(out['match_date'], format='mixed', dayfirst=True, errors='coerce')
    else:                                                         # base / processed format
        out = df.rename(columns=str.lower)
        if not set(REQUIRED_COLUMNS).difference(['season']).issubset(out.columns):
            return None
        out['match_date'] = pd.to_datetime(out['match_date'], errors='coerce')

    if 'season' not in out.columns or out['season'].isna().all():
        out['season'] = _season_from_date(out['match_date'])
    for col in BASE_COLUMNS:
        if col not in out.columns:
            out[col] = np.nan
    return out[BASE_COLUMNS]


def _read_tables(path: Path) -> list:
    """Returns a list of (label, DataFrame) for every table inside a file."""
    ext = path.suffix.lower()
    if ext == ".csv":
        try:
            return [(path.name, pd.read_csv(path, encoding="utf-8-sig"))]
        except UnicodeDecodeError:
            return [(path.name, pd.read_csv(path, encoding="latin-1"))]
    if ext == ".parquet":
        return [(path.name, pd.read_parquet(path))]
    if ext in {".xlsx", ".xls"}:
        sheets = pd.read_excel(path, sheet_name=None)
        return [(f"{path.name} [{name}]", sheet) for name, sheet in sheets.items()]
    if ext in SQLITE_EXTS:
        with sqlite3.connect(path) as conn:
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            return [(f"{path.name} [{t}]", pd.read_sql_query(f'SELECT * FROM "{t}"', conn)) for t in tables]
    return []


def _validate(df: pd.DataFrame, label: str, report: BuildReport) -> pd.DataFrame:
    df = df.copy()
    for col in ['fthg', 'ftag', 'hthg', 'htag', 'home_odds', 'draw_odds', 'away_odds',
                'over_25_odds', 'under_25_odds', 'id']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    for col in ['division', 'ftr', 'htr', 'home_team', 'away_team', 'season']:
        df[col] = df[col].astype('string').str.strip()

    valid = df[REQUIRED_COLUMNS].notna().all(axis=1)
    valid &= df['ftr'].isin(list(RESULT_LABELS)) & df['htr'].isin(list(RESULT_LABELS))
    valid &= (df[['home_odds', 'draw_odds', 'away_odds']] > 0).all(axis=1)
    valid &= (df[['fthg', 'ftag', 'hthg', 'htag']] >= 0).all(axis=1)
    dropped = int((~valid).sum())
    df = df[valid]

    unknown = df.loc[~df['division'].isin(list(LEAGUE_METADATA)), 'division']
    if not unknown.empty:
        codes = ", ".join(sorted(unknown.unique()))
        report.warnings.append(
            f"{label}: skipped {len(unknown)} matches from unknown divisions ({codes}). "
            f"Add them to LEAGUE_METADATA in src/data/schema.py to include them."
        )
        df = df[df['division'].isin(list(LEAGUE_METADATA))]
    if dropped:
        report.warnings.append(f"{label}: dropped {dropped} rows with missing or invalid results/odds.")
    return df


def read_raw(raw_dir: Path = RAW_DIR, report: BuildReport = None) -> pd.DataFrame:
    report = report if report is not None else BuildReport()
    frames = []
    for path in sorted((p for p in raw_dir.iterdir() if p.is_file()), key=lambda p: p.name.lower()):
        ext = path.suffix.lower()
        if ext in IGNORED_EXTS or path.name.startswith('.'):
            continue
        if ext not in TABLE_EXTS | SQLITE_EXTS:
            report.warnings.append(f"{path.name}: unsupported file type, skipped.")
            continue
        try:
            tables = _read_tables(path)
        except Exception as e:  # a broken file should not take the whole dashboard down
            report.warnings.append(f"{path.name}: could not be read ({e}).")
            continue

        file_rows = 0
        for label, table in tables:
            base = _normalise(table)
            if base is None:
                continue
            valid = _validate(base, label, report)
            frames.append(valid)
            file_rows += len(valid)
        if file_rows == 0:
            report.warnings.append(f"{path.name}: no usable matches found (unrecognised columns?).")
        report.files[path.name] = file_rows

    if not frames:
        return pd.DataFrame(columns=BASE_COLUMNS)
    return pd.concat(frames, ignore_index=True)


# ------------------------------------------------------------------------------
# 2. Merging & enrichment
# ------------------------------------------------------------------------------
def merge(df: pd.DataFrame) -> pd.DataFrame:
    """Drops duplicate matches (the file whose name sorts last wins) and assigns ids."""
    df = df.copy()
    df['match_date'] = df['match_date'].dt.strftime('%Y-%m-%d')
    df['id'] = df.groupby(MATCH_KEY)['id'].transform('first')   # a replaced match keeps its id
    df = df.drop_duplicates(subset=MATCH_KEY, keep='last')
    df = df.sort_values(['match_date', 'id', 'division', 'home_team'], na_position='last', kind='stable')

    missing = df['id'].isna()
    start = int(df['id'].max()) + 1 if df['id'].notna().any() else 1
    df.loc[missing, 'id'] = np.arange(start, start + missing.sum())
    if df['id'].duplicated().any():            # ids clashed between files: renumber everything
        df['id'] = np.arange(1, len(df) + 1)
    return df.reset_index(drop=True)


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Adds league metadata and derived features."""
    df = df.copy()
    for col in ['id', 'fthg', 'ftag', 'hthg', 'htag']:
        df[col] = df[col].astype('int64')
    for col in ['division', 'season', 'home_team', 'away_team', 'ftr', 'htr']:
        df[col] = df[col].astype(str)

    df['league_name'] = df['division'].map(lambda d: LEAGUE_METADATA[d]['league'])
    df['country'] = df['division'].map(lambda d: LEAGUE_METADATA[d]['country'])
    df['country_iso3'] = df['division'].map(lambda d: LEAGUE_METADATA[d]['iso3'])

    df['result_label'] = df['ftr'].map(RESULT_LABELS)
    df['ht_result_label'] = df['htr'].map(RESULT_LABELS)
    df['total_goals'] = df['fthg'] + df['ftag']
    df['goal_diff'] = df['fthg'] - df['ftag']
    df['is_over_25'] = (df['total_goals'] > 2.5).astype('int64')
    df['btts'] = ((df['fthg'] > 0) & (df['ftag'] > 0)).astype('int64')

    ht, ft = df['htr'], df['ftr']
    df['match_flow'] = np.select(
        [(ht == 'A') & (ft == 'H'),
         (ht == 'H') & (ft == 'A'),
         (ht == 'D') & (ft == 'H'),
         (ht == 'D') & (ft == 'A'),
         ht == ft],
        ['Home Comeback (Lost HT -> Won FT)',
         'Away Comeback (Lost HT -> Won FT)',
         'Draw HT to Home FT',
         'Draw HT to Away FT',
         'Lead/Draw Maintained'],
        default='Other Flow',
    )

    # Fair probabilities: remove the bookmaker margin from 1/odds
    raw = 1.0 / df[['home_odds', 'draw_odds', 'away_odds']]
    margin = raw.sum(axis=1)
    df['prob_home'] = (raw['home_odds'] / margin).round(4)
    df['prob_draw'] = (raw['draw_odds'] / margin).round(4)
    df['prob_away'] = (raw['away_odds'] / margin).round(4)

    for col in ['home_odds', 'draw_odds', 'away_odds', 'over_25_odds', 'under_25_odds']:
        df[col] = df[col].astype(float).round(2)

    return df[OUTPUT_COLUMNS]


# ------------------------------------------------------------------------------
# 3. Change detection & build
# ------------------------------------------------------------------------------
def _hash_bytes(data: bytes) -> str:
    # Normalise line endings so Windows and macOS checkouts hash the same.
    return hashlib.sha1(data.replace(b"\r\n", b"\n")).hexdigest()


def current_manifest(raw_dir: Path = RAW_DIR) -> dict:
    """What the processed file should have been built from: raw file hashes + pipeline code."""
    code = b"".join(Path(__file__).with_name(n).read_bytes() for n in ("pipeline.py", "schema.py"))
    files = {p.name: _hash_bytes(p.read_bytes())
             for p in sorted(raw_dir.iterdir())
             if p.is_file() and not p.name.startswith('.') and p.suffix.lower() not in IGNORED_EXTS}
    return {"pipeline": _hash_bytes(code), "files": files}


def is_stale() -> bool:
    if not PARQUET_PATH.exists() or not MANIFEST_PATH.exists():
        return True
    try:
        saved = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return True
    return saved != current_manifest()


def build(write: bool = True):
    """Runs the full pipeline. Returns (DataFrame, BuildReport)."""
    report = BuildReport()
    df = read_raw(RAW_DIR, report)
    if df.empty:
        raise ValueError("No usable matches found in data/raw/. " + " ".join(report.warnings))

    df = enrich(merge(df))
    report.rows = len(df)

    if write:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(PARQUET_PATH, index=False)
        MANIFEST_PATH.write_text(json.dumps(current_manifest(), indent=2) + "\n", encoding="utf-8")
    return df, report


if __name__ == "__main__":
    data, rep = build()
    print(f"Built {PARQUET_PATH.relative_to(ROOT)}: {rep.rows:,} matches")
    for name, n in rep.files.items():
        print(f"  {name}: {n:,} valid rows")
    for w in rep.warnings:
        print(f"  ! {w}")
