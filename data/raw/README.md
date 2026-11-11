# data/raw — drop new data here

Every file in this folder is merged into `data/processed/matches.parquet`.
The app rebuilds the dataset automatically when anything here changes. To rebuild by hand, run `python -m src.data.pipeline`.

**Accepted formats**
- football-data.co.uk downloads: a single league `.csv` (e.g. `E0.csv`) or the all-leagues `.xlsx` workbook
- SQLite databases (`.db`, `.sqlite`) whose table uses the base column names
- already-processed `.csv` / `.parquet` files with the base column names, like `base_matches_2023-2025.csv`

Base column names are listed in `src/data/schema.py`.

**Rules**
- If a match (same division, date and teams) appears in several files, the copy from the file whose name sorts last alphabetically is kept.
- Leagues not in `LEAGUE_METADATA` (`src/data/schema.py`) are skipped. The app shows a warning when this happens. Add a line there to include them.
- Rows missing results or 1X2 odds are dropped.
- After adding data, commit both the raw file and the rebuilt `data/processed/` files.
