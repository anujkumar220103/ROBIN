# ROBIN AI

<div align="center">

**Retrieval-Oriented Bot for Intelligent Navigation**

### An AI-powered, multi-tenant knowledge assistant that turns PDF documents into grounded, source-cited answers.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?logo=langchain&logoColor=white)](https://python.langchain.com/)
[![Jina AI](https://img.shields.io/badge/Jina_AI-6C4CF1)](https://jina.ai/embeddings/)
[![Qdrant](https://img.shields.io/badge/Qdrant-DC382D?logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)
[![Groq](https://img.shields.io/badge/Groq-F55036)](https://groq.com/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-000000)](https://openrouter.ai/)
[![PyMuPDF](https://img.shields.io/badge/PyMuPDF-ED1C24)](https://pymupdf.readthedocs.io/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)

[Key Features](#key-features) · [AI/ML Stack](#aiml-technology-stack) · [Architecture](#architecture) · [Quick Start](#quick-start) · [API](#api-overview) · [Deployment](#deployment)

</div>

---

## Overview

ROBIN AI is a full-stack Retrieval-Augmented Generation (RAG) platform for organizations that need accurate answers from private PDF knowledge bases.

Users can upload documents, process them into semantic chunks, generate vector embeddings, retrieve relevant context, and receive answers from supported large language models. Retrieval is isolated per company, so every query uses only the authenticated tenant's knowledge base.

ROBIN also provides an embeddable public chat widget, an internal playground, document management, knowledge-base analytics, and configurable chatbot behavior.

## Key Features

- **Document-grounded RAG** - PDF ingestion, cleaning, token-aware chunking, semantic retrieval, and source-cited generation.
- **Multi-provider LLM fallback** - Google Gemini, Groq, and OpenRouter with configurable provider priority and automatic fallback.
- **Semantic vector search** - Jina AI embeddings stored and retrieved through Qdrant.
- **Tenant isolation** - Documents and vector results are scoped to the authenticated company.
- **Private document storage** - Cloudinary authenticated storage for uploaded PDFs.
- **Secure authentication** - JWT cookies, Argon2id password hashing, and CSRF protection.
- **Public chat widget** - Signed sessions, allowed-domain checks, rate limits, and embed integration.
- **Knowledge-base operations** - Upload, reprocessing, retry, visibility, download, deletion, and ingestion status.
- **Internal playground** - Interactive testing for tenant-specific questions and source responses.
- **Production safeguards** - Health readiness checks, security headers, migrations, request limits, and environment validation.

## AI/ML Technology Stack

ROBIN is primarily an applied AI/ML system built around modern retrieval and generation techniques.

| Component | Technology | Purpose |
|-----------|------------|---------|
| Document parsing | PyMuPDF | Extract text and metadata from PDFs |
| Text processing | LangChain Text Splitters | Clean text and create bounded overlapping chunks |
| Embedding model | `jina-embeddings-v3` | Generate 1024-dimensional document and query vectors through Jina AI |
| Embedding runtime | Jina AI Embeddings API | Keep model weights off the application instance |
| Vector database | Qdrant | Store, search, filter, and isolate tenant vectors |
| RAG orchestration | Custom Python RAG pipeline | Retrieve context, enforce thresholds, build prompts, and validate responses |
| LLM provider 1 | Google Gemini | Grounded answer generation |
| LLM provider 2 | Groq | Fast LLM fallback |
| LLM provider 3 | OpenRouter | OpenAI-compatible model fallback |
| Response reliability | Similarity thresholds and source validation | Reduce unsupported answers and hallucinations |
| Conversation context | Token-limited conversation history | Maintain relevant chat context |

### RAG Pipeline

```text
PDF
  -> Text Extraction
  -> Text Cleaning
  -> Token-Aware Chunking
  -> Jina AI Dense Embedding Generation
  -> Tenant-Scoped Vector Indexing
  -> Question Embedding
  -> Semantic Retrieval
  -> Similarity Filtering
  -> Context Assembly
  -> LLM Generation
  -> Source and Response Validation
  -> Grounded Answer
```

## Architecture

```mermaid
flowchart LR
    U[React User Interface] -->|HTTP, Cookies, CSRF| API[FastAPI Backend]
    API --> DB[(Neon PostgreSQL)]
    API --> PDF[PyMuPDF Document Processing]
    PDF --> CHUNK[LangChain Text Chunking]
    CHUNK --> EMB[Jina AI Embeddings API]
    EMB --> VECTOR[(Qdrant Vector Database)]
    API --> RAG[RAG Retrieval Pipeline]
    VECTOR --> RAG
    RAG --> GEMINI[Google Gemini]
    RAG --> GROQ[Groq]
    RAG --> OPENROUTER[OpenRouter]
    API --> CLOUD[Cloudinary Private Storage]
```

## Dashboard Pages

| Page | Route | Purpose |
|------|-------|---------|
| Landing | `/` | Product introduction and authentication entry |
| Dashboard | `/dashboard` | Knowledge-base overview and quick actions |
| Documents | `/dashboard/documents` | Upload, process, inspect, and manage PDFs |
| Playground | `/dashboard/playground` | Test tenant-specific RAG questions |
| Chatbot Settings | `/dashboard/chatbot-settings` | Configure chatbot identity and behavior |
| Integration | `/dashboard/integration` | Manage public access and embed code |
| Profile | `/dashboard/profile` | View and update account and company details |

## Full Technology Stack

| Layer | Technologies |
|-------|--------------|
| AI/ML | LangChain, Jina AI Embeddings API, Qdrant, Gemini, Groq, OpenRouter |
| Backend | Python 3.12, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic |
| Frontend | React 18, Vite 6, React Router 7, Tailwind CSS 3, Axios |
| Database | Neon PostgreSQL, psycopg 3 |
| Authentication | PyJWT, pwdlib/Argon2id, HTTP-only cookies, CSRF |
| Documents | PyMuPDF, LangChain Text Splitters |
| Storage | Cloudinary private PDF storage |
| Deployment | Render and Vercel |
| Testing | Pytest, FastAPI TestClient, HTTPX |

## Repository Structure

```text
ROBIN/
├── backend/
│   ├── app/
│   │   ├── api/routes/       Authentication, documents, chat, chatbot, and public widget APIs
│   │   ├── core/             Environment and security configuration
│   │   ├── db/               SQLAlchemy engine and database sessions
│   │   ├── models/           Company, user, document, and chatbot models
│   │   ├── rag/              PDF loading, chunking, embeddings, retrieval, and generation
│   │   ├── schemas/          Pydantic request and response models
│   │   └── services/         Authentication and business services
│   ├── alembic/              Database migrations
│   ├── scripts/              Vector and storage migration utilities
│   └── tests/                Backend unit and integration tests
├── frontend/
│   └── src/
│       ├── components/       Shared UI and layout components
│       ├── context/          Authentication state
│       ├── pages/            Dashboard and public widget pages
│       ├── routes/           Protected and public routes
│       └── services/         API clients
├── docs/                     Architecture and development documentation
└── render.yaml               Render backend deployment blueprint
```

## Quick Start

### Prerequisites

- Python 3.12
- Node.js 20 or later
- npm
- Neon PostgreSQL
- Optional: Qdrant Cloud, Cloudinary, and at least one LLM API provider

### 1. Clone the Repository

```powershell
git clone https://github.com/shivamverma30/ROBIN.git
cd ROBIN
```

### 2. Configure the Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Generate two strong secrets:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Minimum local environment values:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
JWT_SECRET_KEY=<generated-jwt-secret>
WIDGET_SESSION_SECRET=<generated-widget-secret>
JINA_API_KEY=<Jina AI API key>
CORS_ORIGINS=["http://localhost:5173"]
```

Apply database migrations and start the API:

```powershell
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

### 3. Configure the Frontend

```powershell
cd ..\frontend
npm install
Copy-Item .env.example .env
npm run dev
```

### 4. Open the Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Readiness check | http://localhost:8000/api/v1/health/ready |

## Environment Variables

### Backend

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Neon pooled PostgreSQL connection string |
| `DATABASE_DIRECT_URL` | No | Direct PostgreSQL connection for migrations |
| `JWT_SECRET_KEY` | Yes | JWT signing secret |
| `WIDGET_SESSION_SECRET` | Yes | Signed public-widget session secret |
| `CORS_ORIGINS` | Yes | JSON array of allowed frontend origins |
| `COOKIE_SECURE` | Production | Set to `true` behind HTTPS |
| `COOKIE_SAMESITE` | Production | Cross-site deployment setting, commonly `none` |
| `QDRANT_URL` | Production | Qdrant Cloud cluster endpoint |
| `QDRANT_API_KEY` | Production | Qdrant Cloud API key |
| `EMBEDDING_PROVIDER` | Yes | Set to `jina` |
| `JINA_API_KEY` | Yes | Jina AI Embeddings API credential |
| `EMBEDDING_MODEL` | Yes | `jina-embeddings-v3` |
| `EMBEDDING_DIMENSION` | Yes | Vector size; defaults to `1024` |
| `EMBEDDING_BATCH_SIZE` | Yes | Bounded embedding request size; defaults to `16` |
| `EMBEDDING_TIMEOUT_SECONDS` | No | Request timeout; defaults to `30` |
| `EMBEDDING_MAX_RETRIES` | No | Bounded retry count; defaults to `3` |
| `EMBEDDING_RETRY_BASE_SECONDS` | No | Exponential retry delay base; defaults to `0.5` |
| `CLOUDINARY_*` | Recommended | Private PDF storage credentials |
| `GEMINI_API_KEY` | Optional | Google Gemini API key |
| `GROQ_API_KEY` | Optional | Groq API key |
| `OPENROUTER_API_KEY` | Optional | OpenRouter API key |

The complete example is available in [`backend/.env.example`](backend/.env.example).

### Frontend

| Variable | Description |
|----------|-------------|
| `VITE_API_BASE_URL` | FastAPI `/api/v1` base URL |

## API Overview

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register a company and administrator |
| `POST` | `/api/v1/auth/login` | Authenticate and set secure cookies |
| `POST` | `/api/v1/auth/logout` | Clear authentication cookies |
| `GET` | `/api/v1/auth/me` | Get the current account |
| `PATCH` | `/api/v1/auth/me` | Update account details |

### RAG and Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST/GET` | `/api/v1/documents/upload` | Upload or list documents |
| `GET/PATCH/DELETE` | `/api/v1/documents/{id}` | Read, update, or delete a document |
| `POST` | `/api/v1/documents/{id}/retry` | Retry failed document ingestion |
| `GET` | `/api/v1/knowledge-base/stats` | Return knowledge-base statistics |
| `POST` | `/api/v1/knowledge-base/search` | Perform tenant-aware semantic search |
| `POST` | `/api/v1/chat/ask` | Ask the internal RAG chatbot |

### Chatbot and Public Widget

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET/PATCH` | `/api/v1/chatbot` | Read or update chatbot configuration |
| `POST` | `/api/v1/chatbot/activate` | Activate the public chatbot |
| `POST` | `/api/v1/chatbot/rotate-id` | Rotate the public chatbot ID |
| `GET` | `/api/v1/public/chatbots/{public_id}/config` | Load public widget configuration |
| `POST` | `/api/v1/public/chatbots/{public_id}/session` | Create a signed widget session |
| `POST` | `/api/v1/public/chatbots/{public_id}/ask` | Ask the public RAG chatbot |

## Testing

Backend:

```powershell
cd backend
python -m pip install -r requirements-dev.txt
python -m pytest -v
```

Frontend:

```powershell
cd frontend
npm run lint
npm run build
```

## Deployment

### Backend on Render

- Python: 3.12
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check: `/api/v1/health/ready`
- Database migration: `alembic upgrade head`

### Frontend on Vercel

- Root directory: `frontend`
- Framework: Vite
- Build command: `npm run build`
- Output: `dist`
- Environment variable: `VITE_API_BASE_URL=https://your-render-service.onrender.com/api/v1`

Configure Neon PostgreSQL, Qdrant Cloud, Cloudinary, and at least one LLM provider before production deployment.

Set `EMBEDDING_PROVIDER=jina`, `JINA_API_KEY`, `EMBEDDING_MODEL=jina-embeddings-v3`,
`EMBEDDING_DIMENSION=1024`, and `EMBEDDING_BATCH_SIZE=16` in the Render service environment.
After deploying the new backend, run `python scripts/reindex_jina_embeddings.py` from
`backend/` once to re-embed existing documents from their stored PDFs. This creates a
separate model/dimension-specific Qdrant collection; the previous MiniLM collection is
left intact. Re-indexing is safe to repeat and processes documents sequentially.

## Security

- Passwords are hashed with Argon2id.
- JWTs are stored in HTTP-only cookies, never browser storage.
- Mutation endpoints use CSRF protection.
- CORS uses explicit allowed origins.
- Database and vector operations preserve company-level tenant isolation.
- PDF downloads require tenant ownership and use authenticated/private storage.
- Document chunks and user queries are sent to Jina AI for embedding; review its data handling and privacy terms before processing confidential content.
- Public widget sessions use signed tokens, domain allowlists, and rate limits.
- Secrets and generated vector/database data are excluded from Git.

## Known Operational Notes

- Logout clears the browser cookie but does not maintain a server-side JWT revocation registry.
- Public and chat limits use application-level counters.
- Jina vectors are written to a model/dimension-specific Qdrant collection; MiniLM vectors are not mixed with them.
- ChromaDB to Qdrant migration requires a separate export and re-indexing procedure.

## Documentation

- [System Architecture](docs/architecture.md)
- [Authentication Flow](docs/authentication-flow.md)
- [Database Design](docs/database-design.md)
- [Development Roadmap](docs/development-roadmap.md)

## Contributing

1. Fork the repository.
2. Create a focused feature branch.
3. Implement and test your changes.
4. Keep API keys and environment secrets out of commits.
5. Open a pull request with clear validation steps.

## License

No license file is currently included. Copyright and usage terms have not yet been specified.

---

<div align="center">
Built for private, document-grounded AI experiences.
</div>
