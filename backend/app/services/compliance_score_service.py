from app.models.enums import RiskCategory, RiskSeverity
from app.schemas.risk import RiskFindingSchema

_SEVERITY_WEIGHTS: dict[RiskSeverity, float] = {
    RiskSeverity.LOW: 5.0,
    RiskSeverity.MEDIUM: 12.0,
    RiskSeverity.HIGH: 25.0,
    RiskSeverity.CRITICAL: 40.0,
}

# Missing clauses are a structural risk (something that should exist doesn't) — weighted
# slightly heavier than an equivalent-severity risk found IN existing text.
_MISSING_CLAUSE_MULTIPLIER = 1.15

_GRADE_BANDS: list[tuple[float, str]] = [(90, "A"), (75, "B"), (60, "C"), (40, "D")]


class ComplianceScoreService:
    """Pure Python, no LLM call — a deterministic weighted aggregate of risk findings."""

    def compute(self, findings: list[RiskFindingSchema]) -> tuple[float, str]:
        if not findings:
            return 100.0, "A"

        score = 100.0
        for finding in findings:
            weight = _SEVERITY_WEIGHTS[finding.severity]
            if finding.category == RiskCategory.MISSING_CLAUSE:
                weight *= _MISSING_CLAUSE_MULTIPLIER
            score -= weight * finding.confidence

        score = max(0.0, min(100.0, score))
        grade = next((letter for threshold, letter in _GRADE_BANDS if score >= threshold), "F")
        return round(score, 1), grade


compliance_score_service = ComplianceScoreService()
