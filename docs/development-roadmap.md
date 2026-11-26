# ROBIN AI — Development Roadmap

## Phase 1: Project Foundation and Frontend Setup ✅ Complete

- FastAPI application with Swagger documentation.
- Pydantic Settings environment configuration.
- Neon PostgreSQL connectivity via SQLAlchemy and psycopg3.
- Alembic migration setup.
- Health check endpoints.
- React frontend with Vite, Tailwind CSS, React Router.
- Professional SaaS landing page.
- Dashboard layout with sidebar navigation.
- All dashboard page stubs (Documents, Playground, Settings, Integration, Profile).

## Phase 2: Secure Authentication and Multi-Tenant Architecture ✅ Complete

- Argon2id password hashing (pwdlib).
- JWT token generation and validation (PyJWT).
- HTTP-only cookie authentication.
- CSRF double-submit cookie protection.
- Company registration (atomic transaction).
- User login and logout.
- Session restoration (GET /auth/me).
- Protected routes (FastAPI dependencies).
- Tenant resolution from authenticated DB user.
- Company profile API.
- User profile update API.
- Multi-tenant isolation enforced at API layer.
- 30 automated backend tests (all passing).
- Frontend ESLint passes (0 warnings).
- Frontend production build passes.

## Phase 3: Document Management and PDF Processing 🔲 Planned

- PDF file upload endpoint.
- File validation and size limits.
- PyMuPDF text extraction.
- Scanned PDF detection.
- Text cleaning pipeline.
- Document status tracking.
- Document listing and deletion APIs.
- Frontend document upload interface.
- Documents page becomes functional.

## Phase 4: Embedding Generation and ChromaDB Integration 🔲 Planned

- HuggingFace Sentence Transformers integration.
- Page-aware text chunking.
- Embedding generation pipeline.
- Tenant-specific ChromaDB collections.
- Chunk storage with metadata.
- Document reprocessing support.
- Vector store management.

## Phase 5: Advanced RAG Pipeline and AI Question Answering 🔲 Planned

- Semantic query embedding.
- Tenant-specific vector retrieval.
- Relevance threshold filtering.
- Context construction with deduplication.
- Gemini API integration.
- Grounded answer generation.
- Source citation validation.
- Insufficient context handling.
- Playground becomes functional.

## Phase 6: Chatbot Configuration and Website Integration 🔲 Planned

- Chatbot settings API and persistence.
- Chatbot name, appearance, welcome message.
- JavaScript embed widget generation.
- Public chatbot endpoint (no auth required for website visitors).
- Integration page becomes functional.
- Chatbot settings page becomes functional.

## Phase 7: Testing, Security, Optimization, and Deployment 🔲 Planned

- Comprehensive integration test suite.
- Load testing.
- PostgreSQL Row-Level Security (defense in depth).
- Rate limiting (distributed, production-grade).
- Production deployment configuration (reverse proxy, HTTPS).
- Environment-specific security hardening.
- Monitoring and logging.
- Documentation finalization.
