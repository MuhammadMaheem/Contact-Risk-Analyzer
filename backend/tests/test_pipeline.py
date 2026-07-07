from pathlib import Path

import pytest

from app.models.enums import DocumentStatus
from app.schemas.analysis import ExtractionResult, PartyItem
from app.schemas.risk import RiskDetectionResult, RiskFindingSchema
from app.schemas.summary import SummaryResult
from app.services.document_processing_pipeline import document_processing_pipeline
from app.services.groq_client_service import groq_client_service

FIXTURES_DIR = Path(__file__).parent / "fixtures"

pytestmark = pytest.mark.asyncio

_FAKE_EXTRACTION = ExtractionResult(
    contract_type="Mutual Non-Disclosure Agreement",
    parties=[PartyItem(name="Northwind Analytics Inc.", role="Disclosing Party")],
    effective_date="March 1, 2026",
    expiry_date="December 31, 2027",
    payment_terms="No fees are payable under this Agreement",
    renewal_clause=None,
    confidentiality_clause="Each Party agrees to hold Confidential Information in strict confidence",
    termination_clause="Continues until December 31, 2027 unless terminated on 30 days notice",
    responsibilities=[],
)

_FAKE_RISKS = RiskDetectionResult(
    findings=[
        RiskFindingSchema(
            category="missing_clause",
            severity="medium",
            confidence=0.8,
            title="No Renewal Clause",
            explanation="The contract does not specify renewal terms.",
            supporting_clause_text=None,
            suggested_action="Add a renewal clause.",
        ),
        RiskFindingSchema(
            category="ambiguous_statement",
            severity="low",
            confidence=0.6,
            title="Undefined Reasonable Efforts",
            explanation="'Reasonable efforts' is not defined.",
            supporting_clause_text="using reasonable efforts, a term left undefined",
            suggested_action="Define reasonable efforts.",
        ),
    ]
)

_FAKE_SUMMARY = SummaryResult(
    executive_summary="A mutual NDA between two companies with a five-year term.",
    key_obligations=["Both parties keep information confidential."],
    important_dates=[{"label": "Expiry Date", "date": "December 31, 2027"}],
    important_clauses=["Confidentiality Clause"],
    recommended_actions=["Add a renewal clause.", "Define reasonable efforts explicitly."],
)


@pytest.fixture
def mocked_groq(monkeypatch):
    async def fake_chat_json(system_prompt, user_content, schema_model, model, temperature=0.1):
        if schema_model is ExtractionResult:
            return _FAKE_EXTRACTION
        if schema_model is RiskDetectionResult:
            return _FAKE_RISKS
        if schema_model is SummaryResult:
            return _FAKE_SUMMARY
        raise AssertionError(f"Unexpected schema requested: {schema_model}")

    monkeypatch.setattr(groq_client_service, "chat_json", fake_chat_json)
    monkeypatch.setattr(groq_client_service, "_client", object())  # bypass "not configured" check


async def test_pipeline_produces_analyzed_document_with_findings(client, auth_headers, mocked_groq):
    content = (FIXTURES_DIR / "sample_nda.txt").read_bytes()
    upload = await client.post(
        "/api/documents",
        headers=auth_headers,
        files={"file": ("sample_nda.txt", content, "text/plain")},
    )
    document_id = upload.json()["document"]["id"]

    await document_processing_pipeline.run(document_id)

    analysis_response = await client.get(f"/api/documents/{document_id}/analysis", headers=auth_headers)
    assert analysis_response.status_code == 200
    analysis = analysis_response.json()
    assert analysis["contract_type"] == "Mutual Non-Disclosure Agreement"
    assert analysis["compliance_grade"] is not None

    risks_response = await client.get(f"/api/documents/{document_id}/risks", headers=auth_headers)
    findings = risks_response.json()
    assert len(findings) == 2
    assert {f["category"] for f in findings} == {"missing_clause", "ambiguous_statement"}

    document_response = await client.get(f"/api/documents/{document_id}", headers=auth_headers)
    assert document_response.json()["status"] == DocumentStatus.ANALYZED.value


async def test_pipeline_marks_document_failed_when_text_too_short_to_analyze(client, auth_headers, mocked_groq):
    # Passes upload validation (non-empty) but is below the parser's minimum-length
    # threshold, so the pipeline should fail it cleanly at the parse stage.
    upload = await client.post(
        "/api/documents",
        headers=auth_headers,
        files={"file": ("too_short.txt", b"Too short.", "text/plain")},
    )
    assert upload.status_code == 202
    document_id = upload.json()["document"]["id"]

    await document_processing_pipeline.run(document_id)

    document_response = await client.get(f"/api/documents/{document_id}", headers=auth_headers)
    body = document_response.json()
    assert body["status"] == DocumentStatus.FAILED.value
    assert "Parsing failed" in body["status_detail"]
