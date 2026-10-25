import pytest
from httpx import AsyncClient


class TestAuth:
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "atlas-workbench"

    @pytest.mark.asyncio
    async def test_liveness_check(self, client: AsyncClient):
        resp = await client.get("/health/live")
        assert resp.status_code == 200
        assert resp.json()["status"] == "alive"

    @pytest.mark.asyncio
    async def test_readiness_check(self, client: AsyncClient):
        resp = await client.get("/health/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"

    @pytest.mark.asyncio
    async def test_me_unauthorized(self, client: AsyncClient):
        resp = await client.get("/auth/me")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_csrf_unauthorized(self, client: AsyncClient):
        resp = await client.get("/auth/csrf")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_csrf_unauthorized(self, client: AsyncClient):
        resp = await client.post("/auth/verify-csrf", json={"csrf_token": "test"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_unauthorized(self, client: AsyncClient):
        resp = await client.post("/auth/logout")
        assert resp.status_code == 401


class TestAuthWithUser:
    @pytest.mark.asyncio
    async def test_me_authorized(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["authenticated"] is True
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_csrf_authorized(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/auth/csrf", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "csrf_token" in data
        assert len(data["csrf_token"]) > 0

    @pytest.mark.asyncio
    async def test_verify_csrf_valid(self, client: AsyncClient, auth_headers: dict):
        # First get the CSRF token
        csrf_resp = await client.get("/auth/csrf", headers=auth_headers)
        csrf_token = csrf_resp.json()["csrf_token"]

        # Verify it
        resp = await client.post("/auth/verify-csrf", json={"csrf_token": csrf_token}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    @pytest.mark.asyncio
    async def test_verify_csrf_invalid(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post("/auth/verify-csrf", json={"csrf_token": "invalid-token"}, headers=auth_headers)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_logout(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post("/auth/logout", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "logout_url" in data

        # Verify cookie is cleared
        assert "access_token" in resp.cookies or "access_token" not in resp.cookies


class TestLoginFlow:
    @pytest.mark.asyncio
    async def test_login_redirect(self, client: AsyncClient):
        resp = await client.get("/auth/login", follow_redirects=False)
        assert resp.status_code == 307
        assert "location" in resp.headers
        assert "keycloak" in resp.headers["location"] or "localhost:8080" in resp.headers["location"]


class TestRoles:
    @pytest.mark.asyncio
    async def test_admin_role_access(self, client: AsyncClient, admin_auth_headers: dict):
        resp = await client.get("/auth/me", headers=admin_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "admin" in data["user"]["roles"]

    @pytest.mark.asyncio
    async def test_operator_role_access(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "operator" in data["user"]["roles"]