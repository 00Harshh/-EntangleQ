"""
ML Prediction Layer — QBER Forecasting
Trains a lightweight model to predict expected QBER from:
  - noise_level: float (0–1)
  - attack_probability: float (0–1)
  - channel_loss: float (0–1)

Uses scikit-learn GradientBoostingRegressor with a synthetic training dataset.
"""

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "qber_model.pkl")


def _generate_training_data(n_samples: int = 5000):
    """
    Synthetic training data based on physics-derived relationships:
      QBER ≈ noise_level * 0.3 + attack_prob * 0.25 + channel_loss * 0.1 + interaction terms
    """
    rng = np.random.default_rng(42)
    noise        = rng.uniform(0, 0.5, n_samples)
    attack_prob  = rng.uniform(0, 1.0, n_samples)
    channel_loss = rng.uniform(0, 0.8, n_samples)

    # Physics-inspired QBER formula
    qber = (
        noise * 0.30
        + attack_prob * 0.25
        + channel_loss * 0.08
        + noise * attack_prob * 0.15      # interaction: noise amplifies attacks
        + rng.normal(0, 0.01, n_samples)  # measurement noise
    )
    qber = np.clip(qber, 0.0, 1.0)

    X = np.column_stack([noise, attack_prob, channel_loss])
    return X, qber


def train_model(force_retrain: bool = False) -> Pipeline:
    """Train and cache the QBER prediction model."""
    if not force_retrain and os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)

    X, y = _generate_training_data()

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("gbr", GradientBoostingRegressor(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42,
        )),
    ])
    model.fit(X, y)
    joblib.dump(model, MODEL_PATH)
    return model


# Module-level model — lazy loaded
_model: Pipeline | None = None


def predict_qber(
    noise_level: float,
    attack_probability: float,
    channel_loss: float,
) -> dict:
    """
    Predict expected QBER and classify threat level.

    Args:
        noise_level:        Physical noise on the quantum channel (0–1)
        attack_probability: Estimated probability of an active attacker (0–1)
        channel_loss:       Photon loss rate in the fiber/channel (0–1)

    Returns:
        dict with predicted_qber, threat_level, recommendation
    """
    global _model
    if _model is None:
        _model = train_model()

    features = np.array([[
        np.clip(noise_level, 0, 1),
        np.clip(attack_probability, 0, 1),
        np.clip(channel_loss, 0, 1),
    ]])

    predicted = float(_model.predict(features)[0])
    predicted = round(np.clip(predicted, 0.0, 1.0), 4)

    # Threat classification
    if predicted < 0.05:
        threat_level = "LOW"
        recommendation = "Proceed with key exchange. Channel is clean."
    elif predicted < 0.11:
        threat_level = "MEDIUM"
        recommendation = "Proceed with caution. Monitor QBER closely."
    elif predicted < 0.20:
        threat_level = "HIGH"
        recommendation = "Eavesdropping likely. Consider aborting or using privacy amplification."
    else:
        threat_level = "CRITICAL"
        recommendation = "Abort key exchange immediately. Channel is compromised."

    return {
        "predicted_qber": predicted,
        "threat_level": threat_level,
        "recommendation": recommendation,
        "inputs": {
            "noise_level": noise_level,
            "attack_probability": attack_probability,
            "channel_loss": channel_loss,
        },
    }


def predict_qber_series(scenarios: list[dict]) -> list[dict]:
    """Batch predict QBER for a list of scenarios."""
    return [
        predict_qber(
            s.get("noise_level", 0),
            s.get("attack_probability", 0),
            s.get("channel_loss", 0),
        )
        for s in scenarios
    ]
