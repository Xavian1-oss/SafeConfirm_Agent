from __future__ import annotations

from dataclasses import dataclass

from safeconfirm.types.models import InterventionType, VerificationScoreModel


@dataclass
class ComparisonResult:
    winner: InterventionType
    scores: dict[str, VerificationScoreModel]
    deltas: dict[str, float]
    mean_score: float


class GroupComparator:
    def compare(self, scores: dict[InterventionType, VerificationScoreModel]) -> ComparisonResult:
        eligible = {k: v for k, v in scores.items() if not v.disqualified}
        pool = eligible or scores
        mean_score = sum(score.total for score in pool.values()) / len(pool)
        deltas = {intervention.value: score.total - mean_score for intervention, score in pool.items()}
        winner_value = max(deltas, key=lambda key: deltas[key])
        winner = InterventionType(winner_value)
        serialized_scores = {intervention.value: score for intervention, score in scores.items()}
        return ComparisonResult(
            winner=winner,
            scores=serialized_scores,
            deltas=deltas,
            mean_score=mean_score,
        )
