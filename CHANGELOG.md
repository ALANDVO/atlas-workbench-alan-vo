# Changelog

## 1.3.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.3.0 — work-in-progress checkpoint

### Added
- Deterministic compression engine (`backend/app/core/compression.py`)
  - Compress mode: abbreviation of verbose phrases, filler word removal
  - Summarize mode: first sentence + key identifiers extraction
  - Off mode: pass-through with no compression
  - MCP recovery references for compressed content
  - Token estimation for original and compressed text
- 26 new backend tests for compression engine (`backend/tests/test_compression_engine.py`)
- Total backend tests: 69 (43 original + 26 new)

Partial code published for continued development. Known issues: STATUS.md.

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

### Added
- POST /compression/sessions/{session_id}/requests endpoint for submitting compression requests
- Session aggregate updates on request submission (totals, eligibility, tokens, savings ratio)
- Stats summary reflects request data across sessions
- 9 new backend tests for request creation and validation (28 compression tests total)

Partial code published for continued development. Known issues: STATUS.md.

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

---

Alan Vo · [alanvo.net](https://alanvo.net)
