# Phase 2 — Authentication and Multi-Tenant Architecture

## Status: ✅ Complete (pending Neon database connection)

## What Was Built

### Security
- Argon2id password hashing via `pwdlib`.
- JWT generation and validation via `PyJWT` (HS256, with issuer/audience/expiry checks).
- HTTP-only JWT cookie.
- Double-submit CSRF cookie protection.

### APIs
| Endpoint | Description |
|----------|-------------|
| POST /api/v1/auth/register | Create company + admin user |
| POST /api/v1/auth/login | Authenticate and set cookies |
| POST /api/v1/auth/logout | Clear cookies |
| GET /api/v1/auth/me | Restore session |
| PATCH /api/v1/auth/me | Update user name |
| GET /api/v1/company/me | Get company info |
| PATCH /api/v1/company/me | Update company name |

### Database
- `companies` and `users` tables with UUID PKs, FK, unique constraints, CHECK role constraint.
- Alembic migration: `001_initial_companies_and_users.py`.

### Frontend
- `AuthContext.jsx` — session state using React Context.
- `useAuth` hook.
- `ProtectedRoute` and `PublicRoute` guards.
- Functional login and registration pages calling real APIs.
- Functional profile page for name and company updates.

## Multi-Tenant Isolation

- `company_id` is derived from the authenticated user's DB record.
- Never accepted from request body, query parameters, or JWT claims.
- FastAPI dependencies (`get_current_user`, `get_current_company`) enforce this.

## Test Results

```
30 passed, 0 failed
```

Tests cover: health endpoints, password hashing, JWT generation/validation,
expired/invalid/tampered token rejection, schema mass-assignment prevention,
tenant isolation principle, slug generation.

## Security Decisions

- Role assigned server-side only — not accepted from registration request.
- Generic "invalid credentials" error — does not reveal email existence.
- Cookie cleared on logout — full revocation not implemented (stateless JWT limitation).
- CSRF uses double-submit cookie — appropriate for SameSite=Lax same-site deployment.

## Known Limitations

- Email verification not implemented.
- Password reset not implemented.
- Rate limiting is in-memory only (not distributed).
- JWT revocation not implemented.

## Phase 3 Prerequisites

Before starting Phase 3:
- Neon database must be configured and migrated.
- Registration and login must be manually verified with the live database.
- File upload library (python-multipart) must be added to requirements.
