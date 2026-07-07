# AI Workflow

This document describes the AI pipeline in detail: prompt design, JSON schemas, and the
failure/degradation behavior of every stage. Prompt source of truth lives in
`backend/app/utils/prompts.py`.

## Pipeline stages

`DocumentProcessingPipeline.run(document_id)` (`backend/app/services/document_processing_pipeline.py`)
runs these stages in order. Every stage catches its own exceptions and writes an `AuditLog`
row — a failure never crashes the request, it degrades the document to a `partial` status
with a human-readable `status_detail`.

| # | Stage | Model / Tool | On failure |
|---|-------|---------------|------------|
| 1 | Parse | pdfplumber / python-docx / plain read, Tesseract OCR fallback | **Fatal** — nothing downstream is possible without text. Document → `failed`. |
| 2 | Chunk + Embed + Index | regex heuristics + `all-MiniLM-L6-v2` + ChromaDB | Non-fatal — semantic search degraded, rest of pipeline continues. |
| 3 | Extract | `llama-3.3-70b-versatile`, JSON mode | Retry once with repair prompt; on total failure, continue to risk detection using raw text. |
| 4 | Risk Detection | `llama-3.3-70b-versatile`, JSON mode | Retry once; on total failure, zero findings persisted, noted in `status_detail`. |
| 5 | Summarize | `llama-3.1-8b-instant` (cheap — synthesizes already-structured JSON, not raw text) | Non-fatal — summary fields left null, UI shows a "summary unavailable" state. |
| 6 | Compliance Score | Pure Python, no LLM call | Can't fail except on empty input (returns neutral 100/A). |
| 7 | Persist + Finalize | — | Document status set to `analyzed` or `partial`; `AuditLog` row written either way. |

A startup sweep (`mark_stale_processing_documents_as_failed`) marks any document still in
`processing` when the server (re)starts as `failed` — cheap crash recovery for the in-process
background-task model.

## Prompt design

Every Groq call goes through `GroqClientService.chat_json(system_prompt, user_content,
schema_model, model)` — a single choke point that requests `response_format={"type":
"json_object"}`, parses with `json.loads`, validates against the target Pydantic model, and
performs **exactly one repair retry** (echoing the invalid output back with the schema) before
raising. This exists because **Groq's JSON mode guarantees syntactically valid JSON but not
schema conformance** — validation errors are treated identically to parse errors.

### Extraction (`AIExtractionService`)

- System prompt instructs zero-hallucination: null/empty for absent fields, quote-or-paraphrase
  the source, no legal advice at this stage.
- Target schema: `ExtractionResult` (`contract_type`, `parties`, `effective_date`, `expiry_date`,
  `payment_terms`, `renewal_clause`, `confidentiality_clause`, `termination_clause`,
  `responsibilities`).
- **Long documents** (>~12k characters): a map-then-merge strategy chunks the text, extracts
  per-chunk with the same prompt, then a cheap `llama-3.1-8b-instant` call consolidates the
  partials into one final `ExtractionResult` (dedupes parties/responsibilities, keeps the most
  complete value per scalar field).

### Risk Detection (`RiskDetectionService`)

The explainability core of the product. The system prompt forces every finding to carry:

- `category`: one of `missing_clause`, `high_risk_condition`, `ambiguous_statement`,
  `unusual_payment_term`, `legal_red_flag`
- `severity`: `low` / `medium` / `high` / `critical`
- `confidence`: 0–1
- `title`, `explanation`: plain-English, human-readable
- `supporting_clause_text`: the exact quoted excerpt, or `null` if the finding is about
  something **missing** from the document
- `suggested_action`: a concrete one-sentence recommendation

The call receives both the raw contract text *and* the structured `ExtractionResult` as
context — the model reasons about missing clauses (e.g. a null `confidentiality_clause` in the
extraction is a strong signal to check for a `missing_clause` finding) rather than only
pattern-matching raw text.

### Summary (`SummarizationService`)

Deliberately synthesizes from the `ExtractionResult` + `RiskDetectionResult` **JSON**, not the
raw document text — this is both cheaper (justifying the `llama-3.1-8b-instant` model) and more
grounded (it can't drift from what was already extracted/flagged). Produces
`executive_summary`, `key_obligations`, `important_dates`, `important_clauses`,
`recommended_actions`.

### Semantic Search & RAG Q&A (`SemanticSearchService`)

One retrieval path serves two modes from a single endpoint (`POST
/api/documents/{id}/search`, `mode: "retrieve" | "answer"`):

1. Embed the user's natural-language query with the same `all-MiniLM-L6-v2` model used at
   indexing time.
2. Query ChromaDB for the top-k chunks belonging to that `document_id` (cosine-similarity-like
   score derived from Chroma's L2 distance).
3. `mode=retrieve` returns the raw chunks — this is the "semantic search" feature.
4. `mode=answer` additionally sends the retrieved excerpts to `llama-3.1-8b-instant` with an
   instruction to answer **using only the provided excerpts**, and say so explicitly if they're
   insufficient — this is the RAG-based Q&A bonus feature, and it's the same underlying
   retrieval as mode 3, so there's no separate index or extra latency for maintaining two
   "features."

## Compliance Score (`ComplianceScoreService`)

No LLM call — a deterministic, auditable formula:

```
score = 100
for each risk finding:
    weight = {low: 5, medium: 12, high: 25, critical: 40}[finding.severity]
    if finding.category == missing_clause:
        weight *= 1.15   # structural risk — something that should exist doesn't
    score -= weight * finding.confidence
score = clamp(score, 0, 100)
grade = A (>=90) / B (>=75) / C (>=60) / D (>=40) / F (<40)
```

## Known limitations

- **Groq JSON-mode reliability**: not schema-enforced by the API itself — mitigated by
  Pydantic validation + one repair retry + documented per-stage degradation, but a
  persistently malformed response still surfaces as a `partial` analysis rather than blocking
  the user.
- **Tesseract OCR accuracy**: no layout/table understanding, sensitive to scan quality/skew.
  Only invoked when a PDF's text layer is empty/too short; `document.used_ocr` is surfaced in
  the UI as a "verify manually" flag. See the README for a note on upgrading to RapidOCR for
  better accuracy on the same CPU-only hardware.
- **Long documents**: extraction uses map-then-merge past ~12k characters; risk detection and
  summary bound their input rather than chunking, which can miss risk language buried very deep
  in extremely long contracts (documented tradeoff for latency/cost).
