import io
import pickle
import logging

import numpy as np

from app.features.schemas import FeatureVector

logger = logging.getLogger(__name__)

# Order must match exactly what we pass into the model
FEATURE_ORDER = [
    "failed_logins_1h",
    "failed_logins_24h",
    "new_device",
    "geo_distance_km",
    "rapid_download_count",
    "secret_file_accesses",
    "denied_attempts",
    "device_trust",
]


def _vector_to_array(vector: FeatureVector) -> np.ndarray:
    """Convert a FeatureVector pydantic model into a numpy array in the right order."""
    data = vector.model_dump()
    return np.array([[data[f] for f in FEATURE_ORDER]], dtype=float)


class MLModel:
    """
    Stage 2 of the scoring pipeline.

    Wraps an IsolationForest model. On day 1, no model file exists so it
    returns a neutral score of 50. Once training/trainer.py runs and saves
    a model, this class loads it from MinIO and uses it for real predictions.

    IsolationForest outputs:
        +1 → normal (inlier)
        -1 → anomaly (outlier)

    We convert that to a 0–100 anomaly probability using the decision_function
    score, which gives a continuous value we can blend with the rule score.
    """

    def __init__(self):
        self._model = None

    def load(self, model_bytes: bytes):
        """Load a pickled model from bytes (called by trainer after downloading from MinIO)."""
        self._model = pickle.loads(model_bytes)
        logger.info("ML model loaded successfully")

    def is_ready(self) -> bool:
        return self._model is not None

    def predict(self, vector: FeatureVector) -> float:
        """
        Returns an anomaly score between 0 and 100.
        0  = perfectly normal
        100 = highly anomalous
        """
        if not self.is_ready():
            # No model trained yet — return neutral score
            # This means ML contributes nothing on day 1 (rule engine carries it)
            logger.debug("ML model not loaded, returning neutral score 50")
            return 50.0

        X = _vector_to_array(vector)

        # decision_function returns negative values for outliers
        # More negative = more anomalous
        raw_score = self._model.decision_function(X)[0]

        # Normalise to 0–100:
        # Typical range is roughly -0.5 (very anomalous) to +0.5 (very normal)
        # We clamp and invert so high = anomalous
        normalised = 1.0 - (raw_score + 0.5)        # shift so 0 = normal
        clamped = max(0.0, min(1.0, normalised))     # clamp 0–1
        return round(clamped * 100, 2)


# Singleton — loaded once at startup and reused
ml_model = MLModel()
