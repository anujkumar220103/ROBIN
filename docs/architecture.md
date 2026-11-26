# ROBIN AI — System Architecture

## Overview

ROBIN AI is a multi-tenant, AI-powered knowledge assistant platform built as a simple modular monolith. Each company (tenant) gets its own logically isolated knowledge base.

## High-Level Architecture

```
Browser (React SPA)
        |
        | HTTP (cookies + CSRF headers)
        v
FastAPI Backend (Python)
        |
        |--- PostgreSQL (Neon Cloud) — users, companies
        |
        |--- ChromaDB (Phase 4) — vector embeddings per tenant
        |
        |--- Gemini API (Phase 5) — LLM for answer generation
```

## Frontend Responsibilities

- Renders UI for all pages (landing, auth, dashboard).
- Manages authentication state using React Context API.
- Calls backend APIs using Axios with `withCredentials: true`.
- Sends the CSRF token in `X-CSRF-Token` header for state-changing requests.
- Routes users based on authentication status.
- Never stores JWTs or passwords in browser storage.

## Backend Responsibilities

- Validates all requests using Pydantic schemas.
- Authenticates users using JWT stored in HTTP-only cookies.
- Enforces tenant isolation — every protected resource query includes the authenticated company ID.
- Hashes passwords with Argon2id via pwdlib.
- Signs JWTs with HS256 using a strong configurable secret.
- Manages database migrations with Alembic.
- Returns controlled errors without exposing internals.

## Neon PostgreSQL Responsibilities

- Stores companies and users tables.
- Enforces uniqueness constraints on email and company slug.
- Provides timezone-aware timestamps (UTC).
- Neon offers both pooled and direct connection endpoints.
  - Pooled: used for normal application queries.
  - Direct: recommended for Alembic migrations.

## Multi-Tenant Architecture

ROBIN AI uses a **shared database with logical tenant isolation** model.

- Every company is a tenant identified by a stable UUID.
- Every user record contains `company_id`.
- Every future company-owned resource (documents, chatbot, conversations) will contain `company_id`.
- Backend derives `company_id` from the authenticated user's database record — never from the frontend request.

```
Company (tenant)
    └── Users
    └── Documents (Phase 3)
    └── Document Chunks (Phase 3)
    └── Chatbot Config (Phase 6)
    └── Conversation History (Phase 6)
    └── ChromaDB Collection (Phase 4) — derived from company UUID
```

## Future ChromaDB Architecture

Each company will have a dedicated ChromaDB collection named after its internal UUID:

```python
# Collection name is derived from stable company UUID, not user-supplied strings.
collection_name = f"company_{company_id.hex}"
```

RAG retrieval will always filter by the company's collection, preventing cross-tenant data leakage.

## Document Ingestion Pipeline (Phase 3–4)

```
PDF Upload
    → File Validation
    → Tenant Ownership Verification
    → PyMuPDF Text Extraction
    → Text Cleaning
    → Page-aware Chunking
    → Embedding Generation (HuggingFace Sentence Transformers)
    → Tenant-specific ChromaDB Collection
    → Document Processing Status Update (PostgreSQL)
```

## Question Answering Pipeline (Phase 5)

```
User Question
    → Chatbot Identification
    → Trusted Tenant Resolution (from authenticated user)
    → Query Embedding
    → Tenant-specific Vector Retrieval (ChromaDB)
    → Relevance Evaluation (threshold filtering)
    → Context Construction (top-K chunks, deduplication)
    → Gemini LLM (grounded answer generation)
    → Source Citation Validation
    → Final Response with References
```

## Security Model

- Passwords: Argon2id hashing (pwdlib).
- Tokens: JWT HS256 with issuer, audience, and expiration validation.
- Transport: HTTP-only cookies (no localStorage).
- CSRF: Double-submit cookie pattern.
- CORS: Explicit allowed origins — no wildcards with credentials.
- Tenant isolation: Company ID always from authenticated DB user record.
- SQL injection: SQLAlchemy ORM parameterized queries only.
- Input validation: Pydantic schemas on all endpoints.
