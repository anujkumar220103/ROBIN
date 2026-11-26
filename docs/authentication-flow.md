# ROBIN AI — Authentication Flow

## Registration

```
POST /api/v1/auth/register
    → Validate input (Pydantic)
    → Normalize email (lowercase)
    → Check email uniqueness
    → Generate company slug
    → Hash password (Argon2id)
    → Create company + user (single transaction)
    → Return 201 with safe user and company info
    → Frontend redirects to /login
```

## Password Hashing

ROBIN AI uses **Argon2id** via the `pwdlib` library.

- Argon2id is the current recommended password hashing algorithm.
- Uses random salt per password — same password produces different hash every time.
- Never stored or logged in plain text.
- Never returned in API responses.

## JWT Generation

On successful login, a signed JWT is generated:

```json
{
  "sub": "user-uuid",
  "iat": 1700000000,
  "exp": 1700003600,
  "iss": "ROBIN AI",
  "aud": "ROBIN AI"
}
```

- Algorithm: HS256 with a strong random secret.
- Expiration: Configurable (default 60 minutes).
- Validation: Signature + expiry + issuer + audience + required claims.

## Cookie Authentication

The JWT is stored in an **HTTP-only cookie**:

```
Set-Cookie: robin_access_token=<jwt>; HttpOnly; SameSite=Lax; Path=/
```

- `HttpOnly`: JavaScript cannot read this cookie.
- `Secure`: True in production (HTTPS only).
- `SameSite=Lax`: Prevents most CSRF while allowing normal navigation.

A separate **CSRF cookie** is also set (not HttpOnly):

```
Set-Cookie: robin_csrf_token=<random>; SameSite=Lax; Path=/
```

## CSRF Protection

ROBIN AI uses the **double-submit cookie pattern**:

1. Backend sets a `robin_csrf_token` cookie (readable by JavaScript).
2. Frontend reads this cookie and adds it as `X-CSRF-Token` header on state-changing requests.
3. Backend verifies the header value matches the cookie value.
4. A cross-site attacker cannot set custom headers, so the check prevents CSRF.

```javascript
// Frontend — har POST/PATCH/DELETE ke saath
headers['X-CSRF-Token'] = getCsrfTokenFromCookie()
```

## Session Restoration

When the React app starts:

```
app starts
    → isInitializing = true
    → GET /api/v1/auth/me
    → 200 OK: restore user + company state
    → 401: set unauthenticated
    → network error: show retry option
    → isInitializing = false
```

This prevents the login page from flashing before a valid session is restored.

## Logout

```
POST /api/v1/auth/logout
    → Verify CSRF token
    → Delete auth cookie
    → Delete CSRF cookie
    → Frontend clears context
    → Redirect to /login
```

**Important limitation**: JWT is stateless. Clearing the cookie prevents the browser from sending it, but the token itself remains valid until expiration. Full server-side revocation (e.g., token blocklist) is outside the current scope.

## Tenant Resolution

Tenant identity is always resolved server-side from the authenticated user's database record:

```python
# dependencies.py
def get_current_company(current_user, db):
    # Company ID user record se milti hai, frontend se nahi
    return db.query(Company).filter(Company.id == current_user.company_id).first()
```

Frontend cannot inject a different company ID through any request parameter.

## Authentication Limitations (Current Phase)

- No email verification.
- No password reset.
- No refresh token rotation.
- No OAuth / social login.
- In-memory rate limiting only (not distributed).
- JWT not revocable before expiration.

These will be addressed in future phases.
