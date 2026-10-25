import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from app.core.config import Settings
from app.core.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def test_settings():
    return Settings(
        database_url=TEST_DATABASE_URL,
        oidc_issuer_url="http://localhost:8080/realms/atlas",
        oidc_client_id="atlas-workbench",
        oidc_client_secret="test-secret",
        oidc_redirect_uri="http://localhost:8000/auth/callback",
        oidc_logout_redirect_uri="http://localhost:5173",
        jwt_secret="test-secret-key-for-testing",
        environment="testing",
        demo_mode=True,
    )


@pytest.fixture(scope="function", autouse=True)
def override_settings(test_settings):
    """Override get_settings to return test settings."""
    with patch("app.core.config.get_settings", return_value=test_settings):
        with patch("app.core.security.settings", test_settings):
            with patch("app.api.auth.settings", test_settings):
                with patch("app.api.health.settings", test_settings):
                    yield


@pytest_asyncio.fixture(scope="function")
async def db_engine(test_settings):
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    async_session = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session):
    user = User(
        keycloak_id="test-keycloak-id",
        email="test@example.com",
        name="Test User",
        roles="operator",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def admin_user(db_session):
    user = User(
        keycloak_id="admin-keycloak-id",
        email="admin@example.com",
        name="Admin User",
        roles="admin",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def create_test_token(user: User, secret: str = "test-secret-key-for-testing") -> str:
    from jose import jwt
    from datetime import datetime, timedelta, timezone

    payload = {
        "sub": str(user.id),
        "email": user.email,
        "name": user.name,
        "roles": [r.value for r in user.get_roles()],
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest_asyncio.fixture(scope="function")
async def auth_headers(test_user):
    token = create_test_token(test_user)
    return {"Authorization": f"Bearer {token}", "Cookie": f"access_token={token}"}


@pytest_asyncio.fixture(scope="function")
async def admin_auth_headers(admin_user):
    token = create_test_token(admin_user)
    return {"Authorization": f"Bearer {token}", "Cookie": f"access_token={token}"}