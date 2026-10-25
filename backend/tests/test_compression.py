import pytest
from httpx import AsyncClient
from uuid import UUID


class TestCompressionSessions:
    @pytest.mark.asyncio
    async def test_create_session(self, client: AsyncClient, auth_headers: dict):
        data = {
            "session_name": "Test Session",
            "mode": "compress",
            "provider": "openai",
            "model": "gpt-4",
        }
        resp = await client.post("/compression/sessions", json=data, headers=auth_headers)
        assert resp.status_code == 201
        session = resp.json()
        assert session["session_name"] == "Test Session"
        assert session["mode"] == "compress"
        assert session["provider"] == "openai"
        assert session["model"] == "gpt-4"
        assert "id" in session
        UUID(session["id"])  # Validate UUID format

    @pytest.mark.asyncio
    async def test_create_session_missing_fields(self, client: AsyncClient, auth_headers: dict):
        data = {"session_name": "Test"}
        resp = await client.post("/compression/sessions", json=data, headers=auth_headers)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_create_session_invalid_mode(self, client: AsyncClient, auth_headers: dict):
        data = {
            "session_name": "Test",
            "mode": "invalid",
            "provider": "openai",
            "model": "gpt-4",
        }
        resp = await client.post("/compression/sessions", json=data, headers=auth_headers)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/compression/sessions", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 20

    @pytest.mark.asyncio
    async def test_list_sessions_with_data(self, client: AsyncClient, auth_headers: dict):
        # Create a few sessions
        for i in range(3):
            await client.post(
                "/compression/sessions",
                json={
                    "session_name": f"Session {i}",
                    "mode": "compress",
                    "provider": "openai",
                    "model": "gpt-4",
                },
                headers=auth_headers,
            )

        resp = await client.get("/compression/sessions", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3

    @pytest.mark.asyncio
    async def test_list_sessions_pagination(self, client: AsyncClient, auth_headers: dict):
        for i in range(5):
            await client.post(
                "/compression/sessions",
                json={
                    "session_name": f"Session {i}",
                    "mode": "compress",
                    "provider": "openai",
                    "model": "gpt-4",
                },
                headers=auth_headers,
            )

        resp = await client.get("/compression/sessions?page=1&page_size=2", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total"] == 5
        assert data["total_pages"] == 3

    @pytest.mark.asyncio
    async def test_list_sessions_filter_by_mode(self, client: AsyncClient, auth_headers: dict):
        await client.post(
            "/compression/sessions",
            json={"session_name": "Compress", "mode": "compress", "provider": "openai", "model": "gpt-4"},
            headers=auth_headers,
        )
        await client.post(
            "/compression/sessions",
            json={"session_name": "Summarize", "mode": "summarize", "provider": "openai", "model": "gpt-4"},
            headers=auth_headers,
        )

        resp = await client.get("/compression/sessions?mode=compress", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["mode"] == "compress"

    @pytest.mark.asyncio
    async def test_list_sessions_filter_by_status_active(self, client: AsyncClient, auth_headers: dict):
        await client.post(
            "/compression/sessions",
            json={"session_name": "Active", "mode": "compress", "provider": "openai", "model": "gpt-4"},
            headers=auth_headers,
        )
        ended_resp = await client.post(
            "/compression/sessions",
            json={"session_name": "To End", "mode": "compress", "provider": "openai", "model": "gpt-4"},
            headers=auth_headers,
        )
        ended_id = ended_resp.json()["id"]
        await client.post(f"/compression/sessions/{ended_id}/end", headers=auth_headers)

        resp = await client.get("/compression/sessions?status=active", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["session_name"] == "Active"
        assert data["items"][0]["ended_at"] is None

    @pytest.mark.asyncio
    async def test_get_session(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post(
            "/compression/sessions",
            json={"session_name": "Get Me", "mode": "compress", "provider": "openai", "model": "gpt-4"},
            headers=auth_headers,
        )
        session_id = create_resp.json()["id"]

        resp = await client.get(f"/compression/sessions/{session_id}", headers=auth_headers)
        assert resp.status_code == 200
        session = resp.json()
        assert session["id"] == session_id
        assert session["session_name"] == "Get Me"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, client: AsyncClient, auth_headers: dict):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(f"/compression/sessions/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_session(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post(
            "/compression/sessions",
            json={"session_name": "Original", "mode": "compress", "provider": "openai", "model": "gpt-4"},
            headers=auth_headers,
        )
        session_id = create_resp.json()["id"]

        resp = await client.patch(
            f"/compression/sessions/{session_id}",
            json={"session_name": "Updated", "mode": "summarize"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        session = resp.json()
        assert session["session_name"] == "Updated"
        assert session["mode"] == "summarize"

    @pytest.mark.asyncio
    async def test_update_ended_session(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post(
            "/compression/sessions",
            json={"session_name": "To End", "mode": "compress", "provider": "openai", "model": "gpt-4"},
            headers=auth_headers,
        )
        session_id = create_resp.json()["id"]
        await client.post(f"/compression/sessions/{session_id}/end", headers=auth_headers)

        resp = await client.patch(
            f"/compression/sessions/{session_id}",
            json={"session_name": "Updated"},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_end_session(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post(
            "/compression/sessions",
            json={"session_name": "To End", "mode": "compress", "provider": "openai", "model": "gpt-4"},
            headers=auth_headers,
        )
        session_id = create_resp.json()["id"]

        resp = await client.post(f"/compression/sessions/{session_id}/end", headers=auth_headers)
        assert resp.status_code == 200
        session = resp.json()
        assert session["ended_at"] is not None

    @pytest.mark.asyncio
    async def test_end_session_twice(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post(
            "/compression/sessions",
            json={"session_name": "To End", "mode": "compress", "provider": "openai", "model": "gpt-4"},
            headers=auth_headers,
        )
        session_id = create_resp.json()["id"]
        await client.post(f"/compression/sessions/{session_id}/end", headers=auth_headers)

        resp = await client.post(f"/compression/sessions/{session_id}/end", headers=auth_headers)
        assert resp.status_code == 400


class TestSessionRequests:
    @pytest.mark.asyncio
    async def test_list_session_requests_empty(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post(
            "/compression/sessions",
            json={"session_name": "Test", "mode": "compress", "provider": "openai", "model": "gpt-4"},
            headers=auth_headers,
        )
        session_id = create_resp.json()["id"]

        resp = await client.get(f"/compression/sessions/{session_id}/requests", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_session_requests_not_found(self, client: AsyncClient, auth_headers: dict):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(f"/compression/sessions/{fake_id}/requests", headers=auth_headers)
        assert resp.status_code == 404


class TestStats:
    @pytest.mark.asyncio
    async def test_get_stats_summary_empty(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/compression/stats/summary", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_sessions"] == 0
        assert data["total_requests"] == 0
        assert data["eligible_requests"] == 0
        assert data["eligibility_rate"] == 0
        assert data["tokens_before"] == 0
        assert data["tokens_after"] == 0
        assert data["tokens_saved"] == 0
        assert data["overall_savings_ratio"] == 0

    @pytest.mark.asyncio
    async def test_get_stats_summary_with_data(self, client: AsyncClient, auth_headers: dict):
        await client.post(
            "/compression/sessions",
            json={"session_name": "Session 1", "mode": "compress", "provider": "openai", "model": "gpt-4"},
            headers=auth_headers,
        )
        await client.post(
            "/compression/sessions",
            json={"session_name": "Session 2", "mode": "summarize", "provider": "anthropic", "model": "claude-3"},
            headers=auth_headers,
        )

        resp = await client.get("/compression/stats/summary", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_sessions"] == 2
        assert data["total_requests"] == 0  # No requests yet


class TestIsolation:
    @pytest.mark.asyncio
    async def test_user_isolation(self, client: AsyncClient, auth_headers: dict, admin_auth_headers: dict):
        # User creates a session
        resp = await client.post(
            "/compression/sessions",
            json={"session_name": "User Session", "mode": "compress", "provider": "openai", "model": "gpt-4"},
            headers=auth_headers,
        )
        session_id = resp.json()["id"]

        # Admin should not see user's session
        resp = await client.get(f"/compression/sessions/{session_id}", headers=admin_auth_headers)
        assert resp.status_code == 404

        # Admin's list should be empty
        resp = await client.get("/compression/sessions", headers=admin_auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0