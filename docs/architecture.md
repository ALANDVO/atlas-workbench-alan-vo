# Atlas Workbench Documentation

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌──────────────┐
│  Coding Agent   │     │  Keycloak    │     │  Keycloak    │
│ (Claude Code,   │────►│  (OIDC/SAML) │     │  SAML IdP    │
│  OpenCode, …)   │     │              │◄───►│  (upstream)  │
└────────┬────────┘     └──────┬───────┘     └──────────────┘
         │                     │
         │ HTTP                │ OIDC Discovery
         ▼                     │
┌────────────────────┐        │
│  Atlas Workbench   │        │
│  Frontend          │        │
│  (React + Vite)    │        │
├────────────────────┤        │
│  Atlas Workbench   │◄───────┘
│  Backend          │
│  (FastAPI)         │
│                    │
│  ┌─────────────┐  │
│  │  Compression│  │
│  │  Sessions   │  │
│  │  API        │  │
│  └─────────────┘  │
│  ┌─────────────┐  │
│  │  Auth API   │  │
│  │  (OIDC)     │  │
│  └─────────────┘  │
│  ┌─────────────┐  │
│  │  SQLAlchemy │  │
│  │  (SQLite)   │  │
│  └─────────────┘  │
└────────────────────┘
```

## API Endpoints

### Health
- `GET /health` — Basic health check
- `GET /health/ready` — Readiness check (verifies database)
- `GET /health/live` — Liveness check

### Authentication (OIDC Keycloak)
- `GET /auth/login` — Initiate OIDC login with PKCE
- `GET /auth/callback` — OIDC callback (code exchange + session creation)
- `POST /auth/logout` — Logout and revoke session
- `GET /auth/me` — Get current user info
- `GET /auth/csrf` — Get CSRF token (requires auth)
- `POST /auth/verify-csrf` — Verify CSRF token (requires auth)

### Compression Sessions
- `POST /compression/sessions` — Create a compression session
- `GET /compression/sessions` — List sessions (with pagination/filtering)
- `GET /compression/sessions/{id}` — Get a specific session
- `PATCH /compression/sessions/{id}` — Update session (name/mode)
- `POST /compression/sessions/{id}/end` — End a session
- `GET /compression/sessions/{id}/requests` — List requests for a session
- `GET /compression/stats/summary` — Aggregated statistics

### Query Parameters
- `page` — Page number (default: 1)
- `page_size` — Items per page (default: 20, max: 100)
- `mode` — Filter by compression mode (compress, summarize, off)

## Database Schema

All models use UUID-as-string primary keys:

- **users** — OIDC subject, email, name, roles, login timestamps
- **sessions** — Session tokens with CSRF, expiry, and audit trail
- **compression_sessions** — Per-user compression sessions with mode, provider, token metrics
- **compression_requests** — Individual request records with token counts and recovery info
- **audit_logs** — Login/logout and resource access audit entries

## Deployment

See `compose.yaml` for full-stack deployment. The compose file includes:
- Backend (FastAPI, nonroot user)
- Frontend (nginx, nonroot user)
- PostgreSQL (persistent volume)
- Keycloak (OIDC provider with realm import)

### TLS

In production, terminate TLS at a reverse proxy (nginx, Caddy, Traefik)
before the application containers. The backend binds to 0.0.0.0:8000
and should only be exposed through the reverse proxy.

### Backup/Restore

PostgreSQL:
```bash
docker compose exec postgres pg_dump -U atlas atlas > backup.sql
docker compose exec postgres psql -U atlas atlas < backup.sql
```

SQLite (development):
```bash
cp ./atlas.db backup.db
```

## SAML / Identity Brokering

Keycloak supports upstream SAML IdPs through identity brokering. The realm
import in `docs/realm-atlas.json` includes a disabled SAML identity provider
template. To configure:

1. Enable the SAML identity provider in the Keycloak admin console
2. Set `singleSignOnServiceUrl` to the upstream IdP's SSO endpoint
3. Configure the IdP with the Keycloak redirect URI (shown in the admin console)
4. Map SAML attributes to Keycloak user properties

The backend validates OIDC ID token signature, issuer, audience, and nonce.
SAML is handled entirely by Keycloak — the application treats Keycloak as the
IdP.