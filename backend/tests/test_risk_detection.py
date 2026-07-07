from app.models.enums import RiskCategory, RiskSeverity
from app.schemas.risk import RiskFindingSchema
from app.services.compliance_score_service import ComplianceScoreService


def _finding(category, severity, confidence) -> RiskFindingSchema:
    return RiskFindingSchema(
        category=category,
        severity=severity,
        confidence=confidence,
        title="Test finding",
        explanation="Because reasons.",
        supporting_clause_text=None,
        suggested_action=None,
    )


def test_confidence_is_clamped_to_valid_range():
    over = _finding(RiskCategory.LEGAL_RED_FLAG, RiskSeverity.HIGH, 1.5)
    under = _finding(RiskCategory.LEGAL_RED_FLAG, RiskSeverity.HIGH, -0.3)
    assert over.confidence == 1.0
    assert under.confidence == 0.0


def test_severity_and_category_enum_coercion_from_string():
    finding = RiskFindingSchema.model_validate(
        {
            "category": "missing_clause",
            "severity": "critical",
            "confidence": 0.9,
            "title": "No termination clause",
            "explanation": "Missing entirely.",
        }
    )
    assert finding.category == RiskCategory.MISSING_CLAUSE
    assert finding.severity == RiskSeverity.CRITICAL


class TestComplianceScoreService:
    def setup_method(self):
        self.service = ComplianceScoreService()

    def test_no_findings_yields_perfect_score(self):
        score, grade = self.service.compute([])
        assert score == 100.0
        assert grade == "A"

    def test_single_low_severity_finding_minor_deduction(self):
        score, grade = self.service.compute(
            [_finding(RiskCategory.AMBIGUOUS_STATEMENT, RiskSeverity.LOW, 1.0)]
        )
        assert score == 95.0
        assert grade == "A"

    def test_critical_findings_drive_score_down_to_failing_grade(self):
        findings = [_finding(RiskCategory.LEGAL_RED_FLAG, RiskSeverity.CRITICAL, 1.0) for _ in range(2)]
        score, grade = self.service.compute(findings)
        assert score == 20.0
        assert grade == "F"

    def test_score_never_goes_below_zero(self):
        findings = [_finding(RiskCategory.LEGAL_RED_FLAG, RiskSeverity.CRITICAL, 1.0) for _ in range(10)]
        score, grade = self.service.compute(findings)
        assert score == 0.0
        assert grade == "F"

    def test_missing_clause_weighted_slightly_heavier_than_equivalent_severity(self):
        missing_score, _ = self.service.compute(
            [_finding(RiskCategory.MISSING_CLAUSE, RiskSeverity.HIGH, 1.0)]
        )
        existing_score, _ = self.service.compute(
            [_finding(RiskCategory.HIGH_RISK_CONDITION, RiskSeverity.HIGH, 1.0)]
        )
        assert missing_score < existing_score
