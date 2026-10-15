# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — 2026-10-15

### Added
- FastAPI backend with health, auth, and compression session endpoints
- React + TypeScript + Vite frontend with dashboard, session list, and create session form
- OIDC authentication via Keycloak (authorization code + PKCE, state+nonce)
- Session management: create, list, get, update, end with pagination and filtering
- Compression statistics summary with token savings tracking
- SQLAlchemy ORM models (users, sessions, compression sessions, requests, audit logs)
- SQLite persistent storage with async SQLAlchemy
- Audit logging for login/logout events
- CI workflow (GitHub Actions): backend pytest, frontend build+test, Docker builds
- Docker Compose with backend, frontend, Keycloak, and PostgreSQL
- Nonroot Dockerfiles for backend (Python) and frontend (nginx)
- Keycloak realm import with operator/analyst/admin roles and SAML IdP template
- Frontend tests with Vitest + Testing Library (App, API client)
- Backend tests with pytest + httpx (health, auth, compression — 24 tests)