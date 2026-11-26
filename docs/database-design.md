# ROBIN AI — Database Design

## Overview

ROBIN AI uses Neon Cloud PostgreSQL. The schema uses UUID primary keys and timezone-aware timestamps (UTC) throughout.

## Entity Relationship

```
companies 1 ──< users (many)
```

One company can have multiple users. Currently, company registration creates exactly one company and one company admin user.

## companies Table

| Column      | Type                     | Constraints                        |
|-------------|--------------------------|-------------------------------------|
| id          | UUID                     | PRIMARY KEY                         |
| name        | VARCHAR(150)             | NOT NULL                            |
| slug        | VARCHAR(180)             | UNIQUE, NOT NULL, INDEXED           |
| is_active   | BOOLEAN                  | DEFAULT true, NOT NULL              |
| created_at  | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now()             |
| updated_at  | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now()             |

**Notes:**
- `slug` is a URL-friendly version of the company name, generated on registration.
- Slug stays stable after registration (not used for authorization).
- Authorization uses `id` (UUID), never the slug.

## users Table

| Column        | Type                     | Constraints                                |
|---------------|--------------------------|---------------------------------------------|
| id            | UUID                     | PRIMARY KEY                                 |
| company_id    | UUID                     | FK → companies.id, NOT NULL, INDEXED        |
| full_name     | VARCHAR(100)             | NOT NULL                                    |
| email         | VARCHAR(255)             | UNIQUE, NOT NULL, INDEXED                   |
| password_hash | TEXT                     | NOT NULL (Argon2id hash)                    |
| role          | VARCHAR(30)              | DEFAULT 'company_admin', CHECK constraint   |
| is_active     | BOOLEAN                  | DEFAULT true, NOT NULL                      |
| created_at    | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now()                     |
| updated_at    | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now()                     |

**Indexes:**
- `ix_users_email` — UNIQUE index for fast email lookups.
- `ix_users_company_id` — index for company membership queries.

**Constraints:**
- `uq_users_email` — unique email globally across all tenants.
- `ck_users_role` — CHECK constraint: `role IN ('company_admin')`.
- `fk_users_company_id` — CASCADE delete (future).

## Alembic Migrations

Migrations are located at `backend/alembic/versions/`.

Initial migration: `001_initial_companies_and_users.py`

Apply with:
```powershell
python -m alembic upgrade head
```

Rollback with:
```powershell
python -m alembic downgrade -1
```

## Future Tables (Phase 3+)

```sql
-- Phase 3
documents (id, company_id, filename, status, created_at, updated_at)
document_chunks (id, document_id, company_id, content, page_number, chunk_index)

-- Phase 6
chatbot_configs (id, company_id, name, welcome_message, primary_color)
conversations (id, company_id, chatbot_id, messages_json, created_at)
```

All future tables will include `company_id` for tenant isolation.

## Row-Level Security (Future Enhancement)

PostgreSQL RLS can provide database-level tenant isolation as a defense-in-depth measure:

```sql
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON documents
  USING (company_id = current_setting('app.company_id')::uuid);
```

This is not currently implemented. Application-level filtering is the primary isolation mechanism.
