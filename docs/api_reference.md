# API Reference

Base URL: `http://localhost:8000` (local dev). All endpoints except `/api/auth/register`,
`/api/auth/login`, and `/api/health` require a `Authorization: Bearer <access_token>` header.
`/api/admin/*` additionally requires the caller's role to be `admin`.

Interactive OpenAPI docs are also available at `/docs` (Swagger UI) and `/redoc` while the
backend is running.

## Auth

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | — | `{email, password, full_name}` → `201 UserProfile` |
| POST | `/api/auth/login` | — | `{email, password}` → `200 {access_token, token_type}` |
| GET | `/api/auth/me` | user | Current user's profile |
| PATCH | `/api/auth/me` | user | `{full_name?, current_password?, new_password?}` → updated profile |

## Documents

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/documents` | user | Multipart `file` upload (pdf/docx/txt, ≤20MB) → `202 {document, message}`; triggers the AI pipeline in the background |
| GET | `/api/documents` | user | List the caller's documents (all documents if admin) with latest analysis summary |
| GET | `/api/documents/{id}` | owner/admin | Single document status/metadata |
| DELETE | `/api/documents/{id}` | owner/admin | Deletes the document, its file, and its vector-store chunks |
| POST | `/api/documents/{id}/reprocess` | owner/admin | Re-runs the AI pipeline, appending a new `Analysis` |

## Analysis

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/documents/{id}/analysis` | owner/admin | Latest `Analysis` (clauses, dates, summary, compliance score) |
| GET | `/api/documents/{id}/risks` | owner/admin | Latest analysis's risk findings |

## Semantic Search / RAG Q&A

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/documents/{id}/search` | owner/admin | `{query, mode: "retrieve"\|"answer", top_k?}` → matching chunks, and a grounded AI answer when `mode=answer` |

## Reports

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/documents/{id}/report` | owner/admin | `{format: "pdf"\|"docx"}` → generates and persists a `Report`, returns its metadata |
| GET | `/api/documents/reports/{report_id}/download` | owner/admin | Streams the generated file |

## Dashboard

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/dashboard/stats` | user | Total documents, average compliance score, high-risk count, frequent risk types, processing history |

## Admin

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/admin/users` | admin | All users with document counts |
| PATCH | `/api/admin/users/{id}` | admin | `{role?, is_active?}` — promote/demote or enable/disable a user |
| GET | `/api/admin/documents` | admin | All documents across all users |
| GET | `/api/admin/logs?level=&limit=` | admin | Audit log / system log entries |
| GET | `/api/admin/stats` | admin | User/document/analysis counts, Groq call count, avg. processing time, documents-by-status breakdown |

## Error shape

Every error response is a consistent JSON envelope, regardless of which layer raised it:

```json
{
  "error_code": "not_found",
  "message": "Document not found",
  "detail": null
}
```

`error_code` values map 1:1 to the exception classes in `backend/app/exceptions.py`
(e.g. `unsupported_file_type`, `file_too_large`, `document_parsing_failed`, `groq_api_error`,
`authentication_failed`, `not_authorized`, `not_found`, `conflict`).
