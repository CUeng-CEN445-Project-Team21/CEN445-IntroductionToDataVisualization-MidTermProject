# European Football Intelligence & Match Dynamics Dashboard
## CEN445 - Introduction to Data Visualization Course Project

An interactive dashboard built with **Python**, **Streamlit** and **Plotly**.

**Data:** 5,420 matches · 8 leagues · 177 teams · Aug 2023 – Jun 2025 (two seasons)

Every chart and model answers one question that no other chart answers.

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

**Sidebar filters** (apply to every chart): leagues, season, total goals, max home odds, comebacks only.

---

### 🚀 Quickstart

```bash
git clone https://github.com/CUeng-CEN445-Project-Team21/CEN445-IntroductionToDataVisualization-MidTermProject.git
cd CEN445-IntroductionToDataVisualization-MidTermProject
pip install -r requirements.txt
streamlit run app.py
```

On Windows you can also double-click `run.bat`.

---

### 📁 Project Structure
```text
├── app.py                 # Entry point: wires the page together
├── data/
│   ├── raw/               # 📥 Drop new data here (CSV / XLSX / SQLite / Parquet)
│   └── processed/         # matches.parquet, rebuilt automatically when raw/ changes
└── src/
    ├── theme.py           # Shared colours (results, leagues)
    ├── data/              # schema, pipeline, loader
    ├── charts/            # One file per chart: build(df), render(df)
    ├── ml/                # clustering.py (ML1), classifier.py (ML2), features.py
    └── ui/                # layout.py (page map), sidebar.py, sections.py, styles.py
```

---

### 👥 Team
* **Necdet Özdemir** - 2021555049 : Charts 1-2-3
* **Yusuf Semih Can** - 2022555475 : Charts 4-5-6
* **Celal Kadir Aydaş** - 2022555006 : Charts 7-8-9
