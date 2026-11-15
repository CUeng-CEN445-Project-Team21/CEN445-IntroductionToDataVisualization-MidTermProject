# CEN445 Midterm Project Report – Team 9

**European Football Intelligence & Match Dynamics Dashboard** · November 2026

## 1. Dataset and Source

The dataset holds **5,420 official matches** from **8 European leagues** and **177 teams**, covering two seasons (August 2023 – June 2025). The leagues are the Premier League (England), La Liga (Spain), Bundesliga (Germany), Serie A (Italy), Ligue 1 (France), Eredivisie (Netherlands), Primeira Liga (Portugal) and Süper Lig (Turkey).

The data comes from [football-data.co.uk](https://www.football-data.co.uk), which publishes match results together with bookmakers' closing 1X2 (home / draw / away) odds. Each row records the date, teams, half-time and full-time scores, and the odds. In preprocessing we dropped rows with missing results or odds, removed duplicate matches, and added derived fields: total goals, goal difference, Over 2.5 and Both Teams to Score flags, half-time → full-time transitions, ISO-3 country codes, and margin-free implied probabilities from the odds.

## 2. Goals of the Analysis

We built an interactive dashboard (Python, Streamlit, Plotly, scikit-learn) in which each chart answers one question no other chart answers. The analysis has four goals:

1. **Compare leagues:** how home advantage and goal output differ across Europe.
2. **Profile teams:** which clubs drive the goals and wins, and who beats whom.
3. **Follow match momentum:** how often the half-time result survives to full time, and whether league trends hold through a season.
4. **Test the betting market:** whether bookmaker odds are accurate, and whether a model using recent results can do better.

## 3. Visualization Techniques

The dashboard has nine charts and two machine learning models. All of them respond to shared sidebar filters (league, season, total goals, maximum home odds, comebacks only).

| # | Technique | Question it answers |
| --- | --- | --- |
| 1 | Choropleth map | Where is home advantage strongest? |
| 2 | Treemap | Which clubs produce the goals and wins in each league? |
| 3 | Sankey diagram | How often does the half-time result hold to full time? |
| 4 | Parallel coordinates | What does each team's full statistical profile look like? |
| 5 | Network graph | Among a league's top 8 teams, who beats whom? |
| 6 | Animated bubble chart | Do league trends hold through the season? |
| 7 | Scoreline heatmap | Which exact scorelines are most common? |
| 8 | Calibration scatter | Are bookmaker odds accurate? |
| 9 | Violin + box plot | How spread out are goals in each league? |
| ML1 | K-Means clustering | Which types of team are there? |
| ML2 | Logistic regression | Do recent results predict a match better than the odds? |

Charts are interactive: hover tooltips, click-to-zoom (treemap), team pinning shared between charts 4 and 5, axis brushing (parallel coordinates), a play button and month slider (bubble chart), and a match simulator (ML2).

## 4. Key Insights and Findings

- **Home advantage is real but uneven.** Home teams won 43.4% of matches, away teams 31.1%, and 25.5% were draws. The gap (home win % − away win %) ranges from +8.4 pp in the Bundesliga to +18.6 pp in the Süper Lig.
- **Leagues split into high- and low-scoring groups.** The Bundesliga (3.18 goals per match), Eredivisie and Premier League (3.11 each) have over 59% of matches with more than 2.5 goals. Serie A (2.59) and La Liga (2.63) stay below 49%, and Serie A has the most draws (28.9%).
- **Half-time leads usually hold.** 72.3% of half-time leads ended as wins. Full comebacks (losing at half-time, winning at full time) happened in only 302 matches, 5.6% of all games.
- **Low scores dominate.** 1–1 is the most common scoreline (12.2%), followed by 1–0 (9.2%) and 2–1 (7.9%).
- **The odds are well calibrated, with a favourite–longshot bias.** Strong favourites win slightly more often than their odds imply, and long shots win less often (for example, away sides priced at 60–67% won 71.7% of the time).
- **Teams form three clear tiers.** K-Means groups the 177 teams into 51 Elite Dominators (56.6% win rate), 90 Balanced Competitors (30.1%) and 36 Relegation Strugglers (16.4%).
- **The market is hard to beat.** On the last 25% of matches (1,229 games), the bookmaker favourite was right 54.6% of the time. Our results-only model reached 53.8%, and adding the odds gave 54.7%, almost equal to the market. All three clearly beat the 42.5% baseline of always picking a home win.

## 5. Repository and Team

**GitHub:** [github.com/CUeng-CEN445-Project-Team21/CEN445-IntroductionToDataVisualization-MidTermProject](https://github.com/CUeng-CEN445-Project-Team21/CEN445-IntroductionToDataVisualization-MidTermProject)

| Member | Student ID | Contribution |
| --- | --- | --- |
| Necdet Özdemir | 2021555049 | Charts 1–3 |
| Yusuf Semih Can | 2022555475 | Charts 4–6 |
| Celal Kadir Aydaş | 2022555006 | Charts 7–9 |
