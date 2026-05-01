from dataclasses import dataclass

from app.core.config import settings
from app.core.enums import RiskLevel, RecommendedAction
from app.features.schemas import FeatureVector
from app.scoring.rules import RuleEngine
from app.scoring.ml_model import ml_model


@dataclass
class ScoreResult:
    rule_score: float
    ml_score: float
    final_score: float
    level: RiskLevel
    recommended_action: RecommendedAction
    fired_rules: list[dict]   # which rules triggered — for explainability


def _score_to_level(score: float) -> RiskLevel:
    """Map a 0–100 score to a risk level."""
    if score <= 20:
        return RiskLevel.LOW
    elif score <= 45:
        return RiskLevel.MEDIUM
    elif score <= 70:
        return RiskLevel.HIGH
    else:
        return RiskLevel.CRITICAL


def _level_to_action(level: RiskLevel) -> RecommendedAction:
    """Map a risk level to a recommended action for consuming services."""
    return {
        RiskLevel.LOW: RecommendedAction.ALLOW,
        RiskLevel.MEDIUM: RecommendedAction.LOG,
        RiskLevel.HIGH: RecommendedAction.MFA_REQUIRED,
        RiskLevel.CRITICAL: RecommendedAction.DENY,
    }[level]


class Scorer:
    """
    Orchestrates the full scoring pipeline:

        feature vector
            → rule engine  (deterministic, explainable)
            → ML model     (probabilistic, pattern-based)
            → weighted blend
            → level + action

    formula:
        final = rule_score * RULE_WEIGHT + ml_score * ML_WEIGHT
        where RULE_WEIGHT=0.6, ML_WEIGHT=0.4 (tunable in config)
    """

    def __init__(self):
        self.rule_engine = RuleEngine()

    def score(self, vector: FeatureVector) -> ScoreResult:
        # Stage 1: rule engine
        rule_score, fired_rules = self.rule_engine.score(vector)

        # Stage 2: ML model
        ml_score = ml_model.predict(vector)

        # Stage 3: weighted blend
        final_score = round(
            rule_score * settings.RULE_WEIGHT + ml_score * settings.ML_WEIGHT, 2
        )
        final_score = min(final_score, 100.0)

        level = _score_to_level(final_score)
        action = _level_to_action(level)

        return ScoreResult(
            rule_score=rule_score,
            ml_score=ml_score,
            final_score=final_score,
            level=level,
            recommended_action=action,
            fired_rules=fired_rules,
        )


# Singleton
scorer = Scorer()
