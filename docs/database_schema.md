# Database Schema

SQLite via SQLAlchemy 2.0 async ORM (`aiosqlite`). Tables created via `Base.metadata.create_all`
on startup — no migration history needed for this greenfield, single-environment scope
(documented tradeoff vs. Alembic).

```mermaid
erDiagram
    USERS ||--o{ DOCUMENTS : owns
    USERS ||--o{ AUDIT_LOGS : triggers
    USERS ||--o{ SEARCH_QUERY_LOGS : asks
    DOCUMENTS ||--o{ ANALYSES : "processed into"
    DOCUMENTS ||--o{ REPORTS : "exported as"
    DOCUMENTS ||--o{ SEARCH_QUERY_LOGS : "searched within"
    ANALYSES ||--o{ RISK_FINDINGS : contains
    ANALYSES ||--o{ REPORTS : "reported from"

    USERS {
        int id PK
        string email UK
        string hashed_password
        string full_name
        enum role "admin | user"
        bool is_active
        datetime created_at
        datetime last_login_at
    }

    DOCUMENTS {
        int id PK
        int owner_id FK
        string original_filename
        string stored_path
        enum file_type "pdf | docx | txt"
        int file_size_bytes
        string sha256_hash
        enum status "uploaded|processing|analyzed|partial|failed"
        text status_detail
        bool used_ocr
        int page_count
        datetime created_at
        datetime processed_at
    }

    ANALYSES {
        int id PK
        int document_id FK
        string contract_type
        json parties
        string effective_date
        string expiry_date
        text payment_terms
        text renewal_clause
        text confidentiality_clause
        text termination_clause
        json responsibilities
        text executive_summary
        json key_obligations
        json important_dates
        json important_clauses
        json recommended_actions
        float compliance_score
        string compliance_grade
        string model_used
        datetime created_at
    }

    RISK_FINDINGS {
        int id PK
        int analysis_id FK
        enum category "missing_clause|high_risk_condition|ambiguous_statement|unusual_payment_term|legal_red_flag"
        enum severity "low|medium|high|critical"
        float confidence
        string title
        text explanation
        text supporting_clause_text
        text suggested_action
    }

    REPORTS {
        int id PK
        int document_id FK
        int analysis_id FK
        enum format "pdf | docx"
        string file_path
        int generated_by_id FK
    }

    AUDIT_LOGS {
        int id PK
        int user_id FK
        string action
        string resource_type
        int resource_id
        json detail
        enum level "info|warning|error"
        datetime created_at
    }

    SEARCH_QUERY_LOGS {
        int id PK
        int document_id FK
        int user_id FK
        text query_text
        string mode
        json result_chunk_ids
        text rag_answer
    }
```

## Which columns feed which feature

| Feature | Query |
|---|---|
| Dashboard: total documents | `count(documents)` scoped by owner (or global for admin) |
| Dashboard: average compliance score | `avg(analyses.compliance_score)` over each document's **latest** analysis |
| Dashboard: high-risk document count | distinct documents whose latest analysis has ≥1 `risk_finding` with severity `high`/`critical` |
| Dashboard: frequently detected risks | `group by risk_findings.category, count(*)` across latest analyses, ordered desc |
| Dashboard / Documents: processing history | `documents` ordered by `created_at desc`, joined to latest `analyses` |
| Admin: system stats | counts across `users`/`documents`/`analyses`, `documents_by_status` group-by, `avg(processed_at - created_at)` for processing time, `groq_client_service.total_calls` (in-process counter) for Groq usage |
| Admin: audit log / system logs | `audit_logs` ordered by `created_at desc`, filterable by `level` |
| Document history | `documents.analyses` relationship (one row per processing run — supports reprocessing without losing prior results) |

`Document.latest_analysis` is a Python property (`analyses[0]` given the relationship is
ordered `Analysis.created_at.desc()`), not a separate column — reprocessing a document appends
a new `Analysis` row rather than overwriting the previous one, so history is preserved.
