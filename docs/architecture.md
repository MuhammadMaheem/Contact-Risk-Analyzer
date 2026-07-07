# Architecture

## Component overview

```mermaid
graph TB
    subgraph Client
        FE["Next.js 15 Frontend<br/>(React 19, Tailwind v4)"]
    end

    subgraph Server["FastAPI Backend"]
        API["API Routes<br/>(auth, documents, analysis, search, reports, dashboard, admin)"]
        PIPE["DocumentProcessingPipeline"]
        SVC["Services<br/>(parser, extraction, risk, summary, embeddings, vector store, compliance, reports)"]
    end

    subgraph Data
        DB[("SQLite<br/>(users, documents, analyses, risk_findings, reports, audit_logs)")]
        CHROMA[("ChromaDB<br/>(persistent, one collection, metadata-filtered by document_id)")]
        FILES[("Local filesystem<br/>(uploads/, generated_reports/)")]
    end

    subgraph External
        GROQ["Groq API<br/>(llama-3.3-70b-versatile, llama-3.1-8b-instant)"]
        TESS["Tesseract OCR<br/>(local, CPU)"]
        MINILM["sentence-transformers<br/>all-MiniLM-L6-v2 (local, CPU)"]
    end

    FE -- "REST (JWT bearer)" --> API
    API --> DB
    API -- "upload triggers" --> PIPE
    PIPE --> SVC
    SVC -- "extraction / risk / summary calls" --> GROQ
    SVC -- "scanned PDFs" --> TESS
    SVC -- "embeddings" --> MINILM
    SVC --> CHROMA
    SVC --> FILES
    PIPE --> DB
```

## Request lifecycle: upload → analyzed

```mermaid
sequenceDiagram
    participant U as User (browser)
    participant API as FastAPI /api/documents
    participant DB as SQLite
    participant BG as BackgroundTasks
    participant PIPE as DocumentProcessingPipeline
    participant GROQ as Groq API
    participant CHROMA as ChromaDB

    U->>API: POST /api/documents (multipart file)
    API->>API: validate extension/size/magic-bytes
    API->>DB: insert Document(status=uploaded)
    API->>BG: schedule pipeline.run(document_id)
    API-->>U: 202 Accepted {document}

    BG->>PIPE: run(document_id)
    PIPE->>DB: status=processing
    PIPE->>PIPE: parse text (pdfplumber/docx/txt, OCR fallback)
    PIPE->>CHROMA: chunk + embed + index (non-fatal on failure)
    PIPE->>GROQ: extract clauses/metadata (JSON mode)
    PIPE->>GROQ: detect risks (JSON mode, uses extraction as context)
    PIPE->>GROQ: summarize (cheap model, uses extraction+risk JSON)
    PIPE->>PIPE: compute compliance score (pure Python)
    PIPE->>DB: insert Analysis + RiskFinding rows, status=analyzed/partial

    loop every ~2.5s
        U->>API: GET /api/documents/{id}
        API-->>U: status
    end
    U->>API: GET /api/documents/{id}/analysis, /risks
    API-->>U: full results
```

## Why these choices

- **SQLite over Postgres**: zero external infra for a local/demo-scoped deployment. Mitigated single-writer limitation with WAL mode + short-lived sessions + one pipeline run at a time. Documented as a scaling limitation, not fixed here — swapping `DATABASE_URL` to a Postgres DSN is the only change needed if concurrency ever matters (SQLAlchemy async already abstracts the driver).
- **In-process `BackgroundTasks` over a task queue**: FastAPI's built-in background tasks are enough for a single-process demo app and avoid a Redis/Celery dependency. Not crash-safe — mitigated with a startup sweep that marks any document stuck in `processing` as `failed` (visible, reprocessable) rather than silently lost. A real deployment would swap this for Celery/RQ.
- **Single ChromaDB collection, metadata-filtered** over one collection per document: simpler lifecycle (no collection cleanup on document delete beyond a `where` filter delete), avoids Chroma collection-count bloat as documents accumulate.
- **Local embeddings (sentence-transformers) instead of Groq/OpenAI embeddings**: Groq doesn't offer an embeddings endpoint; running MiniLM locally (22M params, CPU-friendly) keeps semantic search free and fast without an extra API dependency.
- **CPU-only torch**: this project targets CPU-only machines (no CUDA) — installing the CPU wheel explicitly avoids pulling multi-GB CUDA packages that `sentence-transformers` would otherwise resolve to by default.
