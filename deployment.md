# ROBIN AI — Production Deployment Guide

Ye guide local development se public deployment tak ka simple Hinglish process batati hai.

## 1. Architecture

- Frontend: React/Vite on Vercel
- Backend: FastAPI on Render
- Database: Neon PostgreSQL
- PDF storage: Cloudinary authenticated storage
- Vector database: Qdrant Cloud, local embedded Qdrant fallback ke saath
- Embeddings: Hugging Face `all-MiniLM-L6-v2`
- LLM: Gemini, Groq fallback, OpenRouter fallback

## 2. Prerequisites

1. GitHub account aur repository.
2. Python 3.12, Node.js 20+, npm.
3. Neon, Cloudinary, Qdrant Cloud aur LLM provider accounts.
4. Render aur Vercel accounts.

Real secrets source code mein commit nahi karne hain.

## 3. Neon PostgreSQL

1. Neon mein project aur database banao.
2. Pooled connection string ko `DATABASE_URL` mein set karo.
3. Direct/non-pooled connection ko `DATABASE_DIRECT_URL` mein set karo.
4. URL SSL enabled hona chahiye.

## 4. Cloudinary

1. Cloudinary dashboard se cloud name, API key aur API secret lo.
2. Render environment variables set karo:
   - `CLOUDINARY_CLOUD_NAME`
   - `CLOUDINARY_API_KEY`
   - `CLOUDINARY_API_SECRET`
   - `CLOUDINARY_FOLDER=robin-documents`
3. PDFs `authenticated` mode mein upload hongi. Public URLs expose nahi hongi.

Local PDF migration:

```bash
cd backend
python scripts/migrate_storage_to_cloudinary.py
```

## 5. Qdrant Cloud

1. Qdrant Cloud par cluster banao, region app ke paas choose karo.
2. Cluster endpoint aur API key copy karo; API key ko secret rakho.
3. Render Dashboard → backend service → Environment mein ye values **deployment se pehle** add karo:
   - `QDRANT_URL` — cluster endpoint, including `https://`
   - `QDRANT_API_KEY` — cluster API key
   - `QDRANT_COLLECTION_NAME=robin_vectors`
4. `render.yaml` mein Qdrant variables `sync: false` hain, isliye Blueprint deploy par unhe Render mein configure karna hoga.
5. Local development mein Qdrant URL/key blank reh sakte hain; app `QDRANT_PERSIST_DIR=qdrant_data` mein embedded persistent Qdrant use karegi. Production startup missing Cloud credentials ko reject karega—local disk fallback nahi hoga.

### Chroma se Qdrant migration (sirf existing vectors ke liye)

Naye/empty deployment ke liye migration skip karo. Existing Chroma Cloud/local data ko **backend code deploy karne se pehle** migrate karo, taaki naye backend ko vectors milte rahen. Migration idempotent hai, isliye interruption par ise dobara chala sakte ho.

1. Qdrant Cloud cluster create karke endpoint/key hasil karo.
2. Local `backend/.env` (git-ignored) mein `QDRANT_URL` aur `QDRANT_API_KEY` set karo.
3. Chroma Cloud source ke liye `CHROMA_MIGRATION_SOURCE=cloud`, `CHROMA_API_KEY`, `CHROMA_TENANT`, `CHROMA_DATABASE` set karo. Local source ke liye `CHROMA_MIGRATION_SOURCE=local` aur `CHROMA_PERSIST_DIR` set karo. Ye values `.env` mein hi rakho; commit mat karo.
4. Migration se pehle document uploads/ingestion pause karo aur cutover complete hone tak pause rakho. Agar migration ke dauran ya baad old backend par writes ho jaayen, cutover se pehle migration dobara chalao.

```bash
cd backend
python -m pip install -r requirements-migration.txt
python scripts/migrate_vectors_to_qdrant.py
```

Chroma migration credentials ko Render environment mein add karne ki zaroorat nahi—migration local machine se run hoti hai. Migration complete hone ke baad Qdrant env vars Render mein save karke hi code deploy karo. Chroma source credentials local `backend/.env` mein hi rakho; secrets commit mat karo.

Migration script Chroma source ko modify/delete nahi karti. Qdrant deploy ke baad upload, search, delete aur `/api/v1/health/ready` verify hone tak purana Chroma cluster/credentials rakho; rollback ki zaroorat pade toh purana code unhi se chalega.

Migration ke waqt `EMBEDDING_MODEL` same rakho. Qdrant collection ek vector dimension use karti hai; model/dimension badalna alag re-embedding/re-indexing ka kaam hai.

## 6. LLM Providers

- Gemini: `GEMINI_API_KEY`, `GEMINI_MODEL`
- Groq: `GROQ_API_KEY`, `GROQ_MODEL`
- OpenRouter: `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `OPENROUTER_BASE_URL`
- Order: `LLM_PROVIDER_ORDER=gemini,groq,openrouter`
- Enable: `LLM_ENABLED_PROVIDERS=gemini,groq,openrouter`

Free quotas provider ke account se check karna zaroori hai.

## 7. Security Secrets

Two strong secrets generate karo:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Use these for `JWT_SECRET_KEY` and `WIDGET_SESSION_SECRET`. Production mein weak/missing secrets backend startup ko reject karenge.

## 8. Complete Backend Environment

Minimum production values:

```text
APP_ENV=production
DATABASE_URL=<Neon pooled URL>
DATABASE_DIRECT_URL=<Neon direct URL>
QDRANT_URL=<Qdrant Cloud cluster endpoint>
QDRANT_API_KEY=<Qdrant Cloud API key>
JWT_SECRET_KEY=<strong secret>
WIDGET_SESSION_SECRET=<strong secret>
COOKIE_SECURE=true
COOKIE_SAMESITE=none
CORS_ORIGINS=["https://your-app.vercel.app"]
PUBLIC_WIDGET_URL=https://your-app.vercel.app/widget
EMBEDDING_DEVICE=cpu
MAX_CONCURRENT_INGESTIONS=1
```

Pooled URL aur direct URL ko logs mein print/paste nahi karna.

## 9. Local Verification

```bash
cd backend
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
alembic upgrade head
python -m pytest -q
uvicorn app.main:app --reload
```

Health checks:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/api/v1/health`
- `http://127.0.0.1:8000/api/v1/health/ready`

Frontend:

```bash
cd frontend
npm install
npm run lint
npm run build
npm run dev
```

## 10. GitHub Preparation

Before push:

```bash
git status
git check-ignore backend/.env
git check-ignore uploads/
git check-ignore chroma_data/
git check-ignore qdrant_data/
```

`.env`, uploads, vector data, node_modules, build output aur secrets commit nahi hone chahiye.

## 11. Render Deployment

Option A: repository se Blueprint use karo. `render.yaml` backend service define karta hai.

Option B: manually:

- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Python: 3.12
- Health Check: `/api/v1/health/ready`

Saare environment variables Render Dashboard mein set karo.

## 12. Database Migration on Render

Recommended shell command:

```bash
cd backend
alembic upgrade head
```

Docker deployment `Dockerfile` startup par `alembic upgrade head` bhi run karta hai.

## 13. Vercel Deployment

- Import frontend repository/folder.
- Root Directory: `frontend`
- Framework: Vite
- Build: `npm run build`
- Output: `dist`
- Environment variable:
  `VITE_API_BASE_URL=https://your-render-service.onrender.com/api/v1`

`frontend/vercel.json` SPA routes aur security headers handle karta hai.

## 14. Frontend and Backend Connection

Vercel origin ko backend `CORS_ORIGINS` JSON array mein add karo:

```text
CORS_ORIGINS=["https://your-app.vercel.app","https://www.yourdomain.com"]
```

Cross-origin HTTP-only cookies ke liye production values:

```text
COOKIE_SECURE=true
COOKIE_SAMESITE=none
```

HTTPS deploy URLs required hain.

## 15. Website Widget

Widget integration script ko production backend/public frontend URL ke saath use karo.

Allowed website origins admin configuration mein explicitly list karo. Wildcard origins ko production authorization ke liye trust nahi karna.

## 16. Production Testing

Verify:

1. Registration and login.
2. Logout and cookie expiry.
3. PDF upload, processing, download and delete.
4. Cross-company document isolation.
5. Public chatbot origin restrictions.
6. Public chatbot rate limits.
7. Gemini failure par Groq fallback.
8. Groq failure par OpenRouter fallback.
9. Restart ke baad interrupted ingestion recovery.
10. `/health/ready` database aur vector store status.

## 17. Render Free Tier Notes

Render free web service sleep ho sakti hai. First request slow ho sakta hai. Production demo ke liye paid service ya external uptime monitor consider karo. Uptime monitor sirf public liveness endpoint call kare.

## 18. Free Tier Limitations

Free tiers ab change ho sakte hain. Deploy se pehle official pricing/current limits verify karo:

- Render RAM, CPU, sleep and bandwidth
- Vercel bandwidth and build limits
- Neon compute/storage/branch limits
- Cloudinary transformations, storage and bandwidth
- Qdrant Cloud storage/API limits
- Gemini, Groq and OpenRouter quotas

Card requirement ya paid fallback silently enable mat karna.

## 19. Update Process

```bash
git pull origin main
cd backend
alembic upgrade head
cd ../frontend
npm run build
```

Cloud services auto-deploy settings ke according Render/Vercel se redeploy honge.

## 20. Final Checklist

- [ ] Secrets GitHub/clipboard mein committed nahi hain
- [ ] Neon migration complete
- [ ] Cloudinary credentials configured
- [ ] Qdrant Cloud configured and tested
- [ ] CORS production origin configured
- [ ] Secure cookies configured
- [ ] Render health check green
- [ ] Vercel build green
- [ ] PDF upload/download/delete tested
- [ ] Tenant isolation tested
- [ ] Public widget tested
- [ ] LLM fallback tested
- [ ] Existing local data migration completed
