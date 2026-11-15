"""
ML 2. CLASSIFICATION: Can recent results beat the bookmakers?
Question: does a team's recent record tell you anything the betting odds don't already say?

Two multinomial logistic regressions predict the full-time result (H / D / A):
  * Results-only model   - knows only the two teams' recent results (Elo gap, last-5 form gaps).
                           It never sees the odds.
  * Odds + results model - the same inputs plus the bookmakers' margin-free probabilities.
Both are scored against two benchmarks on the same matches:
  * Base rates           - always predict the most common result (a home win); its
                           probabilities are the result frequencies in the training matches.
  * Bookmaker favourite  - predict the outcome with the shortest odds; its probabilities
                           are the odds themselves.

No look-ahead: features only use earlier matches (src/ml/features.py), and the split is by
date. The models train on the earliest 75% of the filtered matches and are tested on the
latest 25%.

Accuracy = share of results called right. Log-loss = how good the probabilities are (lower is
better). Log-loss is the fairer score here, because a draw is almost never the single most
likely outcome, so no predictor ever "calls" draws.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.data.loader import load_data
from src.ml import features
from src.theme import COLOR_PALETTE, THEME_TEMPLATE

OUTCOMES = ['H', 'D', 'A']
OUTCOME_LABELS = {'H': 'Home win', 'D': 'Draw', 'A': 'Away win'}
OUTCOME_COLORS = {'H': COLOR_PALETTE['home'], 'D': COLOR_PALETTE['draw'], 'A': COLOR_PALETTE['away']}

RESULTS_FEATURES = {
    'elo_diff':      'Elo gap (home − away)',
    'form_pts_diff': 'Points/game gap, last 5',
    'form_gd_diff':  'Goal-diff/game gap, last 5',
}
ODDS_FEATURES = {
    'market_logit': 'Odds: home vs away (log ratio)',
    'prob_draw':    'Odds: draw probability',
}
RESULTS_MODEL = 'Results-only model'
COMBINED_MODEL = 'Odds + results model'
MODELS = {RESULTS_MODEL: RESULTS_FEATURES, COMBINED_MODEL: {**RESULTS_FEATURES, **ODDS_FEATURES}}
BASE_RATES = 'Base rates (always home)'
BOOKMAKER = 'Bookmaker favourite'
PREDICTORS = [BASE_RATES, BOOKMAKER, RESULTS_MODEL, COMBINED_MODEL]   # top-to-bottom chart order

TEST_SHARE = 0.25
MIN_PER_CLASS = 10   # each outcome needs this many training matches
MIN_TEST = 30

MODEL_COLOR = '#2a78d6'       # our models: series blue
BENCHMARK_COLOR = '#898781'   # benchmarks: muted gray, so the models carry the emphasis
SEQ_BLUE = [[0, '#cde2fb'], [0.5, '#5598e7'], [1, '#104281']]
INK_ON_AMBER = '#0b0b0b'      # labels inside the draw (amber) segment need dark ink


# ── Data & training ──────────────────────────────────────────────────────────────────────────

def prepare(df: pd.DataFrame, full: pd.DataFrame) -> pd.DataFrame:
    """Filtered matches + pre-match features (built from `full`), in date order, warm-up removed."""
    data = df.join(features.match_features(full), on='id', how='inner')
    data = data[(data['prior_home'] >= features.WARMUP) & (data['prior_away'] >= features.WARMUP)]
    data = data.dropna(subset=['prob_home', 'prob_draw', 'prob_away', 'ftr', *RESULTS_FEATURES])
    data = data.assign(market_logit=np.log(data['prob_home'] / data['prob_away']))
    return data.sort_values(['match_date', 'id'], kind='stable')


def split(data: pd.DataFrame):
    cut = int(len(data) * (1 - TEST_SHARE))
    train, test = data.iloc[:cut], data.iloc[cut:]
    counts = train['ftr'].value_counts()
    if len(test) < MIN_TEST or any(counts.get(c, 0) < MIN_PER_CLASS for c in OUTCOMES):
        raise ValueError(
            f"The classifier needs at least {MIN_PER_CLASS} home wins, draws and away wins to train on "
            f"and {MIN_TEST} later matches to test on (found H={counts.get('H', 0)}, "
            f"D={counts.get('D', 0)}, A={counts.get('A', 0)}, test={len(test)}). "
            "Broaden the sidebar filters."
        )
    return train, test


def _score(y_true: np.ndarray, proba: np.ndarray) -> dict:
    """proba columns follow OUTCOMES. Accuracy, log-loss, predictions and the confusion matrix."""
    proba = proba / proba.sum(axis=1, keepdims=True)
    true_idx = pd.Series(y_true).map({c: i for i, c in enumerate(OUTCOMES)}).to_numpy()
    pred = np.array(OUTCOMES)[proba.argmax(axis=1)]
    p_true = np.clip(proba[np.arange(len(proba)), true_idx], 1e-15, 1)
    return {
        'accuracy': float((pred == y_true).mean()),
        'log_loss': float(-np.log(p_true).mean()),
        'confusion': confusion_matrix(y_true, pred, labels=OUTCOMES),
    }


def _proba(model, X: pd.DataFrame) -> np.ndarray:
    """predict_proba with columns reordered to OUTCOMES (sklearn sorts classes alphabetically)."""
    order = [list(model.classes_).index(c) for c in OUTCOMES]
    return model.predict_proba(X)[:, order]


@st.cache_data(show_spinner="Training the classifiers...")
def evaluate(data: pd.DataFrame):
    """Fits both models and scores all four predictors on the test window.
    Returns (scores, models, info). Raises ValueError if the filtered data is too thin."""
    train, test = split(data)
    y_test = test['ftr'].to_numpy()

    prior = train['ftr'].value_counts(normalize=True).reindex(OUTCOMES, fill_value=0).to_numpy()
    scores = {
        BASE_RATES: _score(y_test, np.tile(prior, (len(test), 1))),
        BOOKMAKER: _score(y_test, test[['prob_home', 'prob_draw', 'prob_away']].to_numpy()),
    }
    models = {}
    for name, feats in MODELS.items():
        cols = list(feats)
        model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
        model.fit(train[cols], train['ftr'])
        scores[name] = _score(y_test, _proba(model, test[cols]))
        # How much worse the test log-loss gets when one input is shuffled (= how much the model relies on it)
        imp = permutation_importance(model, test[cols], test['ftr'], scoring='neg_log_loss',
                                     n_repeats=20, random_state=42)
        scores[name]['importance'] = pd.DataFrame(
            {'feature': list(feats.values()), 'mean': imp.importances_mean, 'std': imp.importances_std})
        models[name] = model

    info = {
        'n_train': len(train), 'n_test': len(test),
        'train_from': train['match_date'].iloc[0], 'train_to': train['match_date'].iloc[-1],
        'test_from': test['match_date'].iloc[0], 'test_to': test['match_date'].iloc[-1],
    }
    return scores, models, info


# ── Figures ──────────────────────────────────────────────────────────────────────────────────

def comparison_figure(scores: dict, metric: str) -> go.Figure:
    key = 'accuracy' if metric == 'Accuracy' else 'log_loss'
    fmt = (lambda v: f"{v:.1%}") if key == 'accuracy' else (lambda v: f"{v:.3f}")
    fig = go.Figure()
    for group, names, color in (("Benchmarks", [BASE_RATES, BOOKMAKER], BENCHMARK_COLOR),
                                ("Our models", [RESULTS_MODEL, COMBINED_MODEL], MODEL_COLOR)):
        values = [scores[n][key] for n in names]
        fig.add_bar(
            name=group, y=names, x=values, orientation='h', marker_color=color,
            text=[fmt(v) for v in values], textposition='outside', cliponaxis=False,
            customdata=[[scores[n]['accuracy'], scores[n]['log_loss']] for n in names],
            hovertemplate="<b>%{y}</b><br>Accuracy %{customdata[0]:.1%}"
                          "<br>Log-loss %{customdata[1]:.3f}<extra></extra>",
        )
    top = max(scores[n][key] for n in PREDICTORS)
    fig.update_layout(
        template=THEME_TEMPLATE, height=330, bargap=0.35,
        title=dict(text="Results called right (higher is better)" if key == 'accuracy'
                   else "Log-loss of the probabilities (lower is better)", font_size=15),
        xaxis=dict(range=[0, top * 1.18], tickformat='.0%' if key == 'accuracy' else '.2f',
                   showgrid=True, zeroline=False),
        yaxis=dict(categoryorder='array', categoryarray=PREDICTORS[::-1]),
        legend=dict(orientation='h', yanchor='bottom', y=1.0, xanchor='right', x=1),
        margin=dict(l=10, r=10, t=70, b=10),
    )
    return fig


def confusion_figure(cm: np.ndarray, model_name: str) -> go.Figure:
    """Row-normalised: each row shows where that actual result was predicted to go."""
    row_pct = cm / np.maximum(cm.sum(axis=1, keepdims=True), 1) * 100
    labels = [OUTCOME_LABELS[c] for c in OUTCOMES]
    fig = go.Figure(go.Heatmap(
        z=row_pct, x=[f"Predicted {lab.lower()}" for lab in labels], y=[f"Actual {lab.lower()}" for lab in labels],
        customdata=cm, colorscale=SEQ_BLUE, zmin=0, zmax=100, showscale=False, xgap=2, ygap=2,
        texttemplate="%{z:.0f}%<br>(%{customdata})", textfont_size=13,
        hovertemplate="%{y} → %{x}<br>%{customdata} matches (%{z:.0f}% of the row)<extra></extra>",
    ))
    fig.update_layout(
        template=THEME_TEMPLATE, height=330,
        title=dict(text=f"Where each actual result was predicted · {model_name}", font_size=15),
        yaxis=dict(autorange='reversed'), xaxis=dict(side='bottom'),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


def importance_figure(imp: pd.DataFrame, model_name: str) -> go.Figure:
    imp = imp.sort_values('mean')
    fig = go.Figure(go.Bar(
        y=imp['feature'], x=imp['mean'], orientation='h', marker_color=MODEL_COLOR,
        error_x=dict(type='data', array=imp['std'], thickness=1.5, width=4),
        text=[f"+{v:.3f}" if v >= 0 else f"{v:.3f}" for v in imp['mean']],
        textposition='outside', cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Log-loss rises by %{x:.4f} when shuffled<extra></extra>",
    ))
    fig.update_layout(
        template=THEME_TEMPLATE, height=90 + 45 * len(imp), bargap=0.4,
        title=dict(text=f"What the {model_name.lower()} relies on", font_size=15),
        xaxis=dict(title="Rise in test log-loss when the input is shuffled", tickformat='.3f',
                   range=[min(0, imp['mean'].min()) * 1.2, max((imp['mean'] + imp['std']).max(), 1e-3) * 1.35]),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


def forecast_figure(rows: dict) -> go.Figure:
    """One 100% bar per predictor, split into home / draw / away probability."""
    names = list(rows)
    fig = go.Figure()
    for i, outcome in enumerate(OUTCOMES):
        values = [rows[n][i] * 100 for n in names]
        fig.add_bar(
            name=OUTCOME_LABELS[outcome], y=names, x=values, orientation='h',
            marker=dict(color=OUTCOME_COLORS[outcome]),
            text=[f"{v:.0f}%" if v >= 8 else "" for v in values], textposition='inside',
            insidetextanchor='middle',
            textfont_color=INK_ON_AMBER if outcome == 'D' else '#ffffff',
            hovertemplate=f"<b>%{{y}}</b><br>{OUTCOME_LABELS[outcome]}: %{{x:.1f}}%<extra></extra>",
        )
    fig.update_layout(
        template=THEME_TEMPLATE, barmode='stack', height=250, bargap=0.3,
        xaxis=dict(range=[0, 100], ticksuffix='%', showgrid=False),
        yaxis=dict(categoryorder='array', categoryarray=names[::-1]),
        legend=dict(orientation='h', yanchor='bottom', y=1.0, xanchor='left', x=0, traceorder='normal'),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig


# ── Page ─────────────────────────────────────────────────────────────────────────────────────

def _headline(scores: dict) -> str:
    book, res, comb = scores[BOOKMAKER], scores[RESULTS_MODEL], scores[COMBINED_MODEL]
    gap = (book['accuracy'] - res['accuracy']) * 100
    behind = f"{gap:.1f} points behind" if gap > 0.05 else f"{-gap:.1f} points ahead of"
    added = comb['log_loss'] - book['log_loss']
    verdict = ("adds nothing measurable: the odds already price recent form in"
               if added > -0.005 else f"improves the log-loss by {-added:.3f}")
    return (f"💡 Knowing only recent results, the model calls **{res['accuracy']:.1%}** of results right, "
            f"{behind} the bookmakers' favourite ({book['accuracy']:.1%}). "
            f"Putting those results on top of the odds {verdict}.")


def _team_caption(state: pd.Series) -> str:
    return (f"Elo **{state['elo']:.0f}** · last {features.FORM_N}: {state['form_pts']:.1f} pts/game, "
            f"{state['form_gd']:+.1f} goal diff/game")


def _render_simulator(df: pd.DataFrame, full: pd.DataFrame, models: dict):
    st.markdown("##### 🔮 Simulator: what if these two met next?")
    st.caption("Ratings are each team's Elo and last-5 form after its latest match in the dataset. "
               "The odds start at the results-only model's fair price; type a real bookmaker line "
               "to see how much the combined model moves towards it.")

    state = features.team_state(full)
    teams = state.loc[sorted(set(df['home_team']) | set(df['away_team']))]
    teams = teams.sort_values(['league_name', 'elo'], ascending=[True, False])
    options = teams.index.tolist()
    league = df['league_name'].mode().iat[0]
    top_two = teams[teams['league_name'] == league].index[:2].tolist()
    if len(options) < 2 or len(top_two) < 2:
        st.info("The simulator needs at least two teams in the current filter.")
        return
    fmt = lambda t: f"{t} · {teams.at[t, 'league_name']}"

    c_home, c_away = st.columns(2)
    with c_home:
        home = st.selectbox("Home team", options, index=options.index(top_two[0]), format_func=fmt, key="clf_sim_home")
        st.caption(_team_caption(teams.loc[home]))
    with c_away:
        away = st.selectbox("Away team", options, index=options.index(top_two[1]), format_func=fmt, key="clf_sim_away")
        st.caption(_team_caption(teams.loc[away]))
    if home == away:
        st.warning("Pick two different teams.")
        return

    h, a = teams.loc[home], teams.loc[away]
    row = {'elo_diff': h['elo'] - a['elo'], 'form_pts_diff': h['form_pts'] - a['form_pts'],
           'form_gd_diff': h['form_gd'] - a['form_gd']}
    p_results = _proba(models[RESULTS_MODEL], pd.DataFrame([row])[list(RESULTS_FEATURES)])[0]

    # No widget keys on purpose: a new team pair changes the default, which resets the inputs to it.
    fair = [float(np.clip(round(1 / p, 2), 1.05, 25.0)) for p in p_results]
    cols = st.columns(3)
    odds = [col.number_input(f"{OUTCOME_LABELS[c]} odds", min_value=1.05, max_value=25.0,
                             value=v, step=0.05, format="%.2f")
            for col, c, v in zip(cols, OUTCOMES, fair)]
    implied = np.array([1 / o for o in odds])
    p_market = implied / implied.sum()

    row.update(market_logit=np.log(p_market[0] / p_market[2]), prob_draw=p_market[1])
    p_combined = _proba(models[COMBINED_MODEL], pd.DataFrame([row])[list(MODELS[COMBINED_MODEL])])[0]

    st.plotly_chart(forecast_figure({
        "These odds (margin removed)": p_market,
        RESULTS_MODEL: p_results,
        COMBINED_MODEL: p_combined,
    }), width="stretch", config={'displaylogo': False})
    st.caption(f"Margin in these odds: {(implied.sum() - 1):+.1%} "
               "(real bookmaker lines usually carry about +5%; the fair price carries 0%).")


def render(df: pd.DataFrame):
    st.markdown("#### 2️⃣ Logistic Regression: Can Recent Results Beat the Bookmakers?")
    st.caption("Does a team's recent record tell you anything the betting odds don't? "
               "Two models are trained on earlier matches and tested on the latest 25% of the filter.")
    full = load_data()
    try:
        scores, models, info = evaluate(prepare(df, full))
    except ValueError as e:
        st.info(str(e))
        return

    book = scores[BOOKMAKER]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(BOOKMAKER, f"{book['accuracy']:.1%}", help="Pick the outcome with the shortest odds.")
    for col, name in ((m2, RESULTS_MODEL), (m3, COMBINED_MODEL)):
        delta = (scores[name]['accuracy'] - book['accuracy']) * 100
        col.metric(name, f"{scores[name]['accuracy']:.1%}", f"{delta:+.1f} pts vs bookmaker")
    m4.metric("Test matches", f"{info['n_test']:,}",
              help=f"Trained on {info['n_train']:,} matches ({info['train_from']} → {info['train_to']}), "
                   f"tested on the matches from {info['test_from']} to {info['test_to']}.")
    st.markdown(_headline(scores))

    col_a, col_b = st.columns(2)
    with col_a:
        metric = st.segmented_control("Score", ["Log-loss", "Accuracy"], default="Log-loss",
                                      key="clf_metric", label_visibility="collapsed") or "Log-loss"
        st.plotly_chart(comparison_figure(scores, metric), width="stretch", config={'displaylogo': False})
    with col_b:
        model_name = st.segmented_control("Model", list(MODELS), default=RESULTS_MODEL,
                                          key="clf_model", label_visibility="collapsed") or RESULTS_MODEL
        st.plotly_chart(confusion_figure(scores[model_name]['confusion'], model_name),
                        width="stretch", config={'displaylogo': False})

    col_c, col_d = st.columns(2)
    with col_c:
        st.plotly_chart(importance_figure(scores[model_name]['importance'], model_name),
                        width="stretch", config={'displaylogo': False})
    with col_d:
        st.markdown("**Reading the charts**")
        st.markdown(
            f"- **Log-loss** scores the probabilities, not only the pick. Guessing the base rates "
            f"scores {scores[BASE_RATES]['log_loss']:.3f}; lower is better.\n"
            "- **Nobody calls draws.** A draw is rarely the single most likely result, so the Draw "
            "column of the matrix stays nearly empty even for the bookmakers. The draw chance still "
            "shows up in the probabilities (see the simulator).\n"
            "- **Inputs:** Elo rating gap and last-5 form gaps, all from matches *before* kick-off. "
            "The combined model also gets the odds. Each bar on the left is the damage done by "
            "shuffling that one input."
        )
        with st.expander("📋 Scores as a table"):
            st.dataframe(pd.DataFrame({
                'Predictor': PREDICTORS,
                'Accuracy': [scores[n]['accuracy'] for n in PREDICTORS],
                'Log-loss': [scores[n]['log_loss'] for n in PREDICTORS],
            }).style.format({'Accuracy': '{:.1%}', 'Log-loss': '{:.3f}'}), hide_index=True, width="stretch")

    st.divider()
    _render_simulator(df, full, models)
