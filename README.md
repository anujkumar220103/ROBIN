# 🤖 ROBIN AI

<div align="center">

**Retrieval-Oriented Bot for Intelligent Navigation**

Apne PDFs ko AI-powered knowledge base mein badlo aur har sawaal ka grounded, source-backed jawab pao.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-4169E1?logo=postgresql&logoColor=white)](https://neon.tech/)
[![Vector DB](https://img.shields.io/badge/Vector_DB-Qdrant-DC382D)](https://qdrant.tech/)

[Features](#-key-features) · [Architecture](#-architecture) · [Quick Start](#-quick-start) · [API](#-api-overview) · [Deployment](#-deployment) · [Contributing](#-contributing)

</div>

---

## ✨ Key Features

- **Multi-Tenant SaaS** — Har company ke liye isolated users, documents aur vector data.
- **Secure Authentication** — JWT HTTP-only cookies, Argon2id passwords aur CSRF protection.
- **PDF Knowledge Base** — PDF upload, text extraction, cleaning, chunking aur async ingestion.
- **Vector Search** — Hugging Face embeddings ke saath tenant-aware Qdrant retrieval.
- **Multi-Provider RAG** — Gemini, Groq aur OpenRouter support with fallback chain.
- **Grounded Responses** — Context-based answers with similarity checks aur source references.
- **Public Chat Widget** — Signed sessions aur embeddable chatbot jo kisi bhi website par run ho.
- **Chatbot Controls** — Activation, public ID rotation, embed code aur playground.
- **Document Management** — Visibility, download, delete, retry aur ingestion status controls.
- **Production Ready** — Health checks, security headers, migrations, rate limits aur deployment configs.

## 🧭 Dashboard Pages

| Page | Route | Purpose |
|------|-------|---------|
| Landing | `/` | Product introduction aur authentication entry |
| Dashboard | `/dashboard` | Knowledge-base overview aur quick actions |
| Documents | `/dashboard/documents` | PDF upload, processing aur management |
| Playground | `/dashboard/playground` | Internal chatbot testing |
| Chatbot Settings | `/dashboard/chatbot-settings` | Name, welcome message aur activation |
| Integration | `/dashboard/integration` | Widget embed code aur public chatbot controls |
| Profile | `/dashboard/profile` | Account aur company preferences |

## 🏗️ Architecture

```mermaid
flowchart LR
    A[React + Vite] -->|HTTP / Cookies / CSRF| B[FastAPI]
    B --> C[Neon PostgreSQL]
    B --> D[PDF Processing]
    D --> E[Text Chunking]
    E --> F[Sentence Transformers]
    F --> G[Qdrant Vector DB]
    B --> H[RAG Pipeline]
    G --> H
    H --> I[Gemini]
    H --> J[Groq]
    H --> K[OpenRouter]
```

### Document Ingestion

```text
PDF Upload
  → Validation
  → Tenant Ownership Check
  → PyMuPDF Text Extraction
  → Text Cleaning
  → Token-Aware Chunking
  → Embedding Generation
  → Qdrant Indexing
  → PostgreSQL Status Update
```

### Question Answering

```text
Question
  → Tenant & Chatbot Resolution
  → Query Processing
  → Vector Retrieval
  → Similarity Filtering
  → Context Assembly
  → LLM Provider
  → Response Validation
  → Answer + Sources
```

## 🛠️ Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, Vite 6, React Router 7, Tailwind CSS 3, Axios, Lucide |
| Backend | Python 3.12, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic |
| Database | Neon PostgreSQL, psycopg 3 |
| Authentication | PyJWT, pwdlib/Argon2id, HTTP-only cookies, CSRF |
| PDF Processing | PyMuPDF |
| Text Chunking | LangChain Text Splitters |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector Store | Qdrant Cloud or local persistent Qdrant |
| LLM Providers | Google Gemini, Groq, OpenRouter |
| Storage | Cloudinary private PDFs |
| Testing | Pytest, FastAPI TestClient, HTTPX |
| Deployment | Render (backend), Vercel (frontend) |

## 📁 Repository Structure

```text
ROBIN/
├── backend/
│   ├── app/
│   │   ├── api/routes/       Health, auth, company, documents, chat, widget
│   │   ├── core/             Settings and security helpers
│   │   ├── db/               SQLAlchemy engine and session
│   │   ├── models/           Company, user, document and chatbot models
│   │   ├── rag/              PDF, embeddings, retrieval and RAG pipeline
│   │   ├── schemas/          Pydantic request/response models
│   │   └── services/         Authentication and business services
│   ├── alembic/              Database migrations
│   ├── scripts/              Storage and vector migration utilities
│   └── tests/                Backend test suite
├── frontend/
│   └── src/
│       ├── components/       Reusable UI and layout components
│       ├── context/          Authentication state
│       ├── pages/            Dashboard and public widget pages
│       ├── routes/           Protected/public route guards
│       └── services/         API clients
├── docs/                     Architecture and development documentation
├── deployment.md             Production deployment guide
└── render.yaml               Render backend blueprint
```

## 🚀 Quick Start

### Prerequisites

- Python **3.12**
- Node.js **20+**
- npm
- Neon PostgreSQL database
- Optional for full features: Cloudinary, Qdrant Cloud and at least one LLM provider

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

Generate strong secrets:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Minimum local `.env` values:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
JWT_SECRET_KEY=<generated-jwt-secret>
WIDGET_SESSION_SECRET=<generated-widget-secret>
CORS_ORIGINS=["http://localhost:5173"]
```

Apply migrations and start:

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
| Frontend | <http://localhost:5173> |
| Backend API | <http://localhost:8000> |
| Swagger UI | <http://localhost:8000/docs> |
| ReDoc | <http://localhost:8000/redoc> |
| Readiness | <http://localhost:8000/api/v1/health/ready> |

## 🔐 Environment Variables

### Backend

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Neon pooled PostgreSQL URL |
| `DATABASE_DIRECT_URL` | No | Direct URL for migrations |
| `JWT_SECRET_KEY` | Yes | JWT signing secret |
| `WIDGET_SESSION_SECRET` | Yes | Public widget session signing secret |
| `CORS_ORIGINS` | Yes | JSON array of allowed frontend origins |
| `COOKIE_SECURE` | Production | Use `true` behind HTTPS |
| `COOKIE_SAMESITE` | Production | Usually `none` for cross-site cookies |
| `QDRANT_URL` | Production | Qdrant Cloud endpoint |
| `QDRANT_API_KEY` | Production | Qdrant Cloud API key |
| `CLOUDINARY_*` | Recommended | Private PDF storage credentials |
| `GEMINI_API_KEY` | Optional | Google Gemini credentials |
| `GROQ_API_KEY` | Optional | Groq credentials |
| `OPENROUTER_API_KEY` | Optional | OpenRouter credentials |

Complete examples and provider settings are available in [`backend/.env.example`](backend/.env.example).

### Frontend

| Variable | Description |
|----------|-------------|
| `VITE_API_BASE_URL` | FastAPI `/api/v1` base URL |

## 🔌 API Overview

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register company and administrator |
| `POST` | `/api/v1/auth/login` | Login and set secure cookies |
| `POST` | `/api/v1/auth/logout` | Clear authentication cookies |
| `GET` | `/api/v1/auth/me` | Get current account |
| `PATCH` | `/api/v1/auth/me` | Update account profile |

### Core Resources

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET/PATCH` | `/api/v1/company/me` | Read or update company |
| `POST/GET` | `/api/v1/documents/upload` | Upload and list documents |
| `GET/PATCH/DELETE` | `/api/v1/documents/{id}` | Document operations |
| `POST` | `/api/v1/documents/{id}/retry` | Retry failed ingestion |
| `GET` | `/api/v1/knowledge-base/stats` | Knowledge-base statistics |
| `POST` | `/api/v1/knowledge-base/search` | Tenant-aware vector search |
| `POST` | `/api/v1/chat/ask` | Ask the internal chatbot |
| `GET/PATCH` | `/api/v1/chatbot` | Read or update chatbot settings |
| `POST` | `/api/v1/chatbot/activate` | Activate public chatbot |
| `POST` | `/api/v1/chatbot/rotate-id` | Rotate public widget ID |

### Public Widget

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/public/chatbots/{public_id}/config` | Load widget configuration |
| `POST` | `/api/v1/public/chatbots/{public_id}/session` | Create signed public session |
| `POST` | `/api/v1/public/chatbots/{public_id}/ask` | Ask the public chatbot |

## 🧪 Testing

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

## 🌐 Deployment

Production setup is documented in [`deployment.md`](deployment.md).

### Backend — Render

- Python: **3.12**
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check: `/api/v1/health/ready`
- Migration: `alembic upgrade head`

### Frontend — Vercel

- Root: `frontend`
- Framework: Vite
- Build: `npm run build`
- Output: `dist`
- Environment: `VITE_API_BASE_URL=https://your-render-service.onrender.com/api/v1`

Before deployment, configure Neon PostgreSQL, Qdrant Cloud, Cloudinary and at least one LLM provider in the backend environment.

## 🔒 Security

- Passwords are hashed with Argon2id.
- JWTs are stored in HTTP-only cookies, never browser storage.
- Mutation endpoints use CSRF protection.
- CORS allows explicit origins only.
- Database queries preserve company-level tenant isolation.
- PDF downloads use tenant ownership validation and authenticated/private storage.
- Public widget sessions use signed, short-lived tokens and origin/rate limits.
- Secrets and vector/database data are excluded from Git.

## ⚠️ Known Operational Notes

- JWT logout clears the browser cookie; it does not maintain a server-side token revocation registry.
- Public and chat limits use application-level counters.
- A vector collection dimension must remain compatible with the configured embedding model.
- Migrating from ChromaDB to Qdrant requires the migration procedure in [`deployment.md`](deployment.md).

## 📚 Documentation

- [System Architecture](docs/architecture.md)
- [Authentication Flow](docs/authentication-flow.md)
- [Database Design](docs/database-design.md)
- [Development Roadmap](docs/development-roadmap.md)
- [Production Deployment](deployment.md)

## 🤝 Contributing

1. Fork the repository.
2. Create a focused branch:
   ```powershell
   git checkout -b feature/my-feature
   ```
3. Implement and test your changes.
4. Keep secrets out of commits.
5. Open a Pull Request with a clear description and validation steps.

## 📄 License

No license file is currently included. Copyright and usage terms have not yet been specified.

---

<div align="center">
Built with ❤️ for document-grounded AI experiences.
</div>
