"""
ML 2. CLASSIFICATION: Match Outcome Prediction & Feature Importance
Logistic Regression predicting H / D / A from market odds, plus a live simulator.
"""

import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from src.theme import THEME_TEMPLATE

FEATURES = ['prob_home', 'prob_draw', 'prob_away', 'home_odds', 'draw_odds', 'away_odds']
MIN_PER_CLASS = 10  # each outcome needs enough examples to train and test on


def train_match_classifier(df: pd.DataFrame):
    """
    Trains a Logistic Regression model to predict match outcomes (H, D, A)
    from market odds and derived probabilities.
    Returns: (accuracy, model, scaler, cm_fig, importance_fig). Raises ValueError if data is too thin.
    """
    clean_df = df.dropna(subset=['prob_home', 'prob_draw', 'prob_away', 'ftr']).copy()

    counts = clean_df['ftr'].value_counts()
    if any(counts.get(c, 0) < MIN_PER_CLASS for c in ['H', 'D', 'A']):
        raise ValueError(
            f"The classifier needs at least {MIN_PER_CLASS} home wins, draws and away wins in the "
            f"current filter (found H={counts.get('H', 0)}, D={counts.get('D', 0)}, A={counts.get('A', 0)}). "
            "Broaden the sidebar filters."
        )

    X = clean_df[FEATURES]
    y = clean_df['ftr']  # 'H', 'D', 'A'

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    acc = accuracy_score(y_test, y_pred)

    # 1. Confusion Matrix Figure
    labels = ['H', 'D', 'A']
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    cm_df = pd.DataFrame(cm, index=['Actual Home', 'Actual Draw', 'Actual Away'],
                         columns=['Pred Home', 'Pred Draw', 'Pred Away'])

    cm_fig = px.imshow(
        cm_df,
        text_auto=True,
        color_continuous_scale='Blues',
        title=f"🤖 ML 2: Confusion Matrix (Accuracy: {acc:.1%})"
    )
    cm_fig.update_layout(template=THEME_TEMPLATE, height=380, margin=dict(l=10, r=10, t=50, b=10))

    # 2. Feature Importance Figure (Home Win Coefficients)
    home_idx = list(model.classes_).index('H')
    coefs = model.coef_[home_idx]
    feat_df = pd.DataFrame({'Feature': FEATURES, 'Weight': coefs}).sort_values('Weight', ascending=True)

    imp_fig = px.bar(
        feat_df,
        x='Weight',
        y='Feature',
        orientation='h',
        color='Weight',
        color_continuous_scale='Tealrose',
        title="🤖 ML 2: Feature Weights Driving Home Win Prediction"
    )
    imp_fig.update_layout(template=THEME_TEMPLATE, height=380, margin=dict(l=10, r=10, t=50, b=10))

    return acc, model, scaler, cm_fig, imp_fig


def _render_simulator(model, scaler):
    st.markdown("##### 🔮 Live Match Prediction Simulator")
    sim_col1, sim_col2, sim_col3 = st.columns(3)
    with sim_col1:
        sim_h = st.number_input("Simulated Home Odds:", min_value=1.05, max_value=25.0, value=1.75, step=0.05)
    with sim_col2:
        sim_d = st.number_input("Simulated Draw Odds:", min_value=1.05, max_value=25.0, value=3.60, step=0.05)
    with sim_col3:
        sim_a = st.number_input("Simulated Away Odds:", min_value=1.05, max_value=25.0, value=4.50, step=0.05)

    # Fair probabilities
    raw_h, raw_d, raw_a = 1.0 / sim_h, 1.0 / sim_d, 1.0 / sim_a
    m = raw_h + raw_d + raw_a
    p_h, p_d, p_a = raw_h / m, raw_d / m, raw_a / m

    sim_input = pd.DataFrame([{
        'prob_home': p_h, 'prob_draw': p_d, 'prob_away': p_a,
        'home_odds': sim_h, 'draw_odds': sim_d, 'away_odds': sim_a
    }])
    sim_scaled = scaler.transform(sim_input[FEATURES])
    pred_probs = model.predict_proba(sim_scaled)[0]
    prob_dict = dict(zip(model.classes_, pred_probs))

    pcol1, pcol2, pcol3 = st.columns(3)
    pcol1.metric("Predicted Home Win Prob", f"{prob_dict.get('H', 0):.1%}")
    pcol2.metric("Predicted Draw Prob", f"{prob_dict.get('D', 0):.1%}")
    pcol3.metric("Predicted Away Win Prob", f"{prob_dict.get('A', 0):.1%}")


def render(df: pd.DataFrame):
    st.markdown("#### 2️⃣ Logistic Regression: Outcome Prediction & Feature Importance")
    try:
        acc, model, scaler, cm_fig, imp_fig = train_match_classifier(df)
    except ValueError as e:
        st.info(str(e))
        return

    col_g, col_h = st.columns(2)
    with col_g:
        st.plotly_chart(cm_fig, width="stretch")
    with col_h:
        st.plotly_chart(imp_fig, width="stretch")

    _render_simulator(model, scaler)
