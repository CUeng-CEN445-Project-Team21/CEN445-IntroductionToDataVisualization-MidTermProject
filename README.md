# European Football Intelligence & Match Dynamics Dashboard
## CEN445 - Introduction to Data Visualization Course Project

An interactive dashboard built with **Python**, **Streamlit** and **Plotly**.

**Data:** 5,420 matches · 8 leagues · 177 teams · Aug 2023 – Jun 2025 (two seasons)

Every chart and model answers one question that no other chart answers. Only chart #8 and ML2 look at the betting odds. Team-level stats appear only in #2, #4, #5 and ML1, and each of those looks at them from a different angle.

---

### 📊 Charts & Models

| # | Chart | Owner | Question it answers | How to interact |
|---|-------|-------|---------------------|-----------------|
| 1 | Choropleth map | Necdet Özdemir | Where is home advantage strongest? | Hover a country (value printed on each) |
| 2 | Treemap | Necdet Özdemir | Which clubs produce the goals and wins in each league? | Click a league to zoom |
| 3 | Sankey | Necdet Özdemir | How often does the half-time result hold to full-time? | Hover a flow |
| 4 | Parallel coordinates | Yusuf Semih Can | What does each team's full statistical profile look like? | Hover a line, click to pin a team; click an axis bar to highlight a range; league pills |
| 5 | Network graph | Yusuf Semih Can | Among a league's top teams, who beats whom? | Click a team to pin it (shared with #4); click an arrow for that head-to-head; league selectbox |
| 6 | Animated bubble chart | Yusuf Semih Can | Do league trends hold through the season? | Play button + month slider; click a bubble to draw its Aug → May path |
| 7 | Score heatmap | Celal Kadir Aydaş | Which exact scorelines are most common? | Count / % pills; zone filter |
| 8 | Calibration scatter | Celal Kadir Aydaş | Are bookmaker odds accurate? | Market pills (H / D / A); ±3 pp band toggle |
| 9 | Violin + box plot | Celal Kadir Aydaş | How spread out are goals in each league? | Sort pills; 2.5 / 3.5 benchmark line |
| ML1 | K-Means clustering | — | Which types of team are there? | k slider (2–4); rate teams within their own league |
| ML2 | Logistic regression | — | How well do recent results and the odds predict a result? | Model and score switches; match simulator (pick two teams) |

---

### 🎨 What each chart shows

"pp" = percentage points.

| # | One mark = | Position | Colour | Size |
|---|-----------|----------|--------|------|
| 1 | One country (league) | `country_iso3` on the map | Home advantage = home win % − away win % (runs from +8.3 pp in the Bundesliga to +18.6 pp in the Süper Lig) ⚠️ *in progress: the map is still coloured by average goals* | — |
| 2 | One team inside its league | Nested tiles: All → league → team | Wins | Area = goals scored |
| 3 | One HT → FT flow | Left = `htr`, right = `ftr` | Lead held / comeback / shift | Width = matches |
| 4 | One team | 7 axes: points per game, goals scored / match, goals conceded / match, win %, draw %, clean-sheet %, BTTS % | Points per game | — |
| 5 | One of a league's top 8 teams (most wins, home + away) | Circle | Net wins inside the group (wins − losses) | Node = wins inside the group; arrow = wins in that pairing |
| 6 | One league in one month | X = home win % so far, Y = avg goals so far | League | Matches played so far |
| 7 | One scoreline (0–5 × 0–5) | X = away goals, Y = home goals | Match count or % | — |
| 8 | One probability bin (15 bins) | X = implied probability, Y = share that happened | Value (> +2 pp) / fair / overpriced (< −2 pp) | Matches in the bin |
| 9 | One league's goal distribution; outlier dots = single matches | X = league (sorted by mean goals), Y = total goals | League | — |
| ML1 | One team | X = goals scored / match, Y = goals conceded / match (reversed) | Cluster (tier) | Win rate |
| ML2 | Confusion-matrix cell; feature-importance bar | Predicted vs actual result | Count | — |

**How the derived fields are computed**
- Team stats (#4, #5, ML1) come from a table with one row per team per match. For the home side, goals for = `fthg` and goals against = `ftag`. For the away side, the two are swapped. Teams with fewer than 15 matches in the current filters are left out. Under the default filters, all 177 teams have at least 15.
- Season month (#6): Aug = 1 … May = 10. The few June matches count as May. Each point is a running total up to and including that month. With "All seasons", both seasons are pooled by season month.
- ML1 scales three features (goals scored / match, goals conceded / match, win %) and groups the teams with K-Means. Tiers are ranked by win %.
- ML2 trains two multinomial logistic regressions on the earliest 75 % of matches and tests them on the latest 25 %. The first sees only recent results (Elo gap and last-5 form). The second also sees the bookmakers' probabilities. Both are compared with two baselines: base rates and the bookmaker favourite. Features only use matches played earlier, so there is no look-ahead.

---

### 🧭 Using the dashboard

- **Sidebar filters** (apply to every chart, model and KPI): leagues, season, total goals, max home odds, comebacks only. Use **Reset filters** to go back to the defaults.
- **KPI row** at the top shows matches, average goals per match, home win %, over 2.5 goals % and both-teams-scored %.
- **Visual Analysis** tab has three chart groups (Charts 1–3, 4–6 and 7–9). **Machine Learning** tab has ML1 and ML2.
- **Pinned teams** are shared by charts #4 and #5. Click a team in either chart and it is highlighted in both.
- At the bottom, **Explore the filtered data** shows the filtered rows and lets you download them as CSV.

---

### 🚀 Quickstart

Requires Python 3.10+.

```bash
git clone https://github.com/CUeng-CEN445-Project-Team21/CEN445-IntroductionToDataVisualization-MidTermProject.git
cd CEN445-IntroductionToDataVisualization-MidTermProject
pip install -r requirements.txt
streamlit run app.py
```

On Windows, you can also double-click `run.bat`. The first time it runs, it creates a `.venv` and installs the dependencies. After that, it starts the dashboard on the first free port from 8501.

---

### 🗂️ Data

- Source: [football-data.co.uk](https://www.football-data.co.uk) results and closing 1X2 odds.
- To add data, put a file in `data/raw/`. Accepted formats are CSV, XLSX, SQLite and Parquet. The app rebuilds `data/processed/matches.parquet` automatically, or you can run `python -m src.data.pipeline` by hand. See [data/raw/README.md](data/raw/README.md) for the rules.
- Known leagues and the column contract are in [src/data/schema.py](src/data/schema.py).

---

### 📁 Project Structure
```text
├── app.py                 # Entry point: wires the page together
├── run.bat                # Windows one-click launcher
├── requirements.txt
├── .streamlit/config.toml # Page theme (light + dark)
├── data/
│   ├── raw/               # 📥 Drop new data here (CSV / XLSX / SQLite / Parquet)
│   └── processed/         # matches.parquet, rebuilt automatically when raw/ changes
└── src/
    ├── theme.py           # Shared colours (results, leagues)
    ├── data/              # schema.py, pipeline.py, loader.py
    ├── charts/            # One file per chart: build(df) + render(df); interaction.py = shared clicks
    ├── ml/                # clustering.py (ML1), classifier.py (ML2), features.py (Elo + form)
    └── ui/                # layout.py (page map), sidebar.py, sections.py, styles.py
```

**To add a chart:** copy an existing file in `src/charts/`, change `build()`, then add it to `src/ui/layout.py`.

---

### 👥 Team
* **Necdet Özdemir** - 2021555049 : Charts 1-2-3
* **Yusuf Semih Can** - 2022555475 : Charts 4-5-6
* **Celal Kadir Aydaş** - 2022555006 : Charts 7-8-9
