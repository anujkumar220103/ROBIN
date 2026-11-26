# ROBIN AI

**Retrieval-Oriented Bot for Intelligent Navigation**

A multi-tenant, AI-powered knowledge assistant platform. Companies upload business documents, build an intelligent knowledge base, and deploy chatbots that answer questions grounded in those documents.

---

## Implementation Status

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Project Foundation and Frontend | ✅ Complete |
| Phase 2 | Secure Authentication and Multi-Tenant Architecture | ✅ Complete (requires Neon DB) |
| Phase 3 | Document Management and PDF Processing | 🔲 Planned |
| Phase 4 | Embedding Generation and ChromaDB Integration | 🔲 Planned |
| Phase 5 | Advanced RAG Pipeline and AI Question Answering | 🔲 Planned |
| Phase 6 | Chatbot Configuration and Website Integration | 🔲 Planned |
| Phase 7 | Testing, Security, Optimization, and Deployment | 🔲 Planned |

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Tailwind CSS, React Router, Axios |
| Backend | Python 3.14, FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| Database | Neon Cloud PostgreSQL, psycopg3, Alembic |
| Auth | JWT (PyJWT), Argon2id (pwdlib), HTTP-only cookies |
| Testing | Pytest, FastAPI TestClient, HTTPX |
| Future AI | LangChain, Gemini, HuggingFace, ChromaDB, PyMuPDF |

---

## Repository Structure

```
robin-ai/
├── frontend/               React SPA
│   ├── src/
│   │   ├── components/     Reusable UI components and layout
│   │   ├── context/        Authentication context (React Context API)
│   │   ├── hooks/          useAuth hook
│   │   ├── pages/          All application pages
│   │   ├── routes/         ProtectedRoute and PublicRoute
│   │   ├── services/       Axios API service modules
│   │   └── App.jsx         Root with routing
│   ├── .env.example
│   └── package.json
│
├── backend/                FastAPI application
│   ├── app/
│   │   ├── api/            Routes and dependencies
│   │   ├── core/           Config and security utilities
│   │   ├── db/             SQLAlchemy base, engine, session
│   │   ├── models/         ORM models (Company, User)
│   │   ├── schemas/        Pydantic request/response schemas
│   │   ├── services/       Business logic
│   │   └── main.py         Application entry point
│   ├── alembic/            Database migrations
│   ├── tests/              Automated tests (30 tests)
│   ├── .env.example
│   └── requirements.txt
│
├── docs/                   Documentation
│   ├── architecture.md
│   ├── authentication-flow.md
│   ├── database-design.md
│   ├── development-roadmap.md
│   ├── phase-1.md
│   └── phase-2.md
│
└── .gitignore
```

---

## Prerequisites

- Python 3.14 (or 3.11/3.12)
- Node.js 18+ and npm
- A Neon Cloud PostgreSQL account

---

## Neon Database Setup

1. Go to [neon.tech](https://neon.tech) and create a free account.
2. Create a new project named `robin-ai`.
3. Select a region close to you.
4. Note the connection string — format:
   ```
   postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
   ```
5. Copy this into `backend/.env` as `DATABASE_URL`.
6. Optionally set `DATABASE_DIRECT_URL` for a direct (non-pooled) connection for migrations.

---

## Backend Setup

```powershell
cd backend

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

Copy-Item .env.example .env
```

Edit `backend/.env`:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
JWT_SECRET_KEY=<generate below>
```

**Generate JWT secret:**
```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

**Apply migrations:**
```powershell
python -m alembic upgrade head
```

**Start backend:**
```powershell
python -m uvicorn app.main:app --reload
```

---

## Frontend Setup

```powershell
cd frontend

npm install
Copy-Item .env.example .env
npm run dev
```

---

## Development URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Neon PostgreSQL connection string |
| `DATABASE_DIRECT_URL` | No | Direct connection for migrations |
| `JWT_SECRET_KEY` | Yes | Random 64-char secret |
| `JWT_ALGORITHM` | No | Default: HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Default: 60 |
| `COOKIE_SECURE` | No | Set `true` in production |
| `CORS_ORIGINS` | No | Default: `["http://localhost:5173"]` |

### Frontend (`frontend/.env`)

| Variable | Description |
|----------|-------------|
| `VITE_API_BASE_URL` | Backend API URL |

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | Public | Root liveness check |
| GET | `/api/v1/health` | Public | Service health |
| GET | `/api/v1/health/db` | Public | Database health |
| POST | `/api/v1/auth/register` | Public | Register company + admin |
| POST | `/api/v1/auth/login` | Public | Login and set cookies |
| POST | `/api/v1/auth/logout` | CSRF | Clear cookies |
| GET | `/api/v1/auth/me` | Cookie | Current user and company |
| PATCH | `/api/v1/auth/me` | Cookie+CSRF | Update user name |
| GET | `/api/v1/company/me` | Cookie | Get company profile |
| PATCH | `/api/v1/company/me` | Cookie+CSRF | Update company name |

---

## Authentication Flow

1. User registers → company + admin user created atomically.
2. User logs in → JWT set as HTTP-only cookie + CSRF cookie.
3. Frontend reads CSRF cookie → adds `X-CSRF-Token` header on mutations.
4. On page refresh → frontend calls `/auth/me` to restore session.
5. User logs out → both cookies cleared.

---

## Running Tests

```powershell
cd backend
python -m pip install -r requirements-dev.txt
python -m pytest -v
```

**Expected output:** `30 passed`

---

## Frontend Verification

```powershell
cd frontend
npm run lint     # 0 warnings expected
npm run build    # production build
```

---

## Security Notes

- Never commit `.env` files.
- Use a randomly generated `JWT_SECRET_KEY` (at least 32 characters).
- Set `COOKIE_SECURE=true` in production.
- Run behind HTTPS in production.
- Do not add wildcard CORS origins when cookies are enabled.

---

## Known Limitations

- JWT is stateless — logout clears the cookie but does not revoke the token.
- Rate limiting is in-memory only.
- No email verification.
- No password reset.
- Dashboard pages for Documents, Playground, Settings, and Integration are stubs (Phase 3–6).
