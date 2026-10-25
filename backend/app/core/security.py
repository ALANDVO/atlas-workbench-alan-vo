import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode
import httpx
from jose import jwt, JWTError
from pydantic import BaseModel
from app.core.config import get_settings

settings = get_settings()


class TokenData(BaseModel):
    sub: str
    email: str
    name: str
    roles: list[str]
    exp: int
    iat: int
    nonce: Optional[str] = None


class OIDCConfig(BaseModel):
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str
    userinfo_endpoint: str
    end_session_endpoint: str


_oidc_config: Optional[OIDCConfig] = None


async def get_oidc_config() -> OIDCConfig:
    global _oidc_config
    if _oidc_config is not None:
        return _oidc_config

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.oidc_issuer_url}/.well-known/openid-configuration",
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        _oidc_config = OIDCConfig(
            issuer=data["issuer"],
            authorization_endpoint=data["authorization_endpoint"],
            token_endpoint=data["token_endpoint"],
            jwks_uri=data["jwks_uri"],
            userinfo_endpoint=data["userinfo_endpoint"],
            end_session_endpoint=data["end_session_endpoint"],
        )
        return _oidc_config


def create_state() -> str:
    return secrets.token_urlsafe(32)


def create_nonce() -> str:
    return secrets.token_urlsafe(32)


def build_authorization_url(state: str, nonce: str) -> str:
    oidc_config = OIDCConfig(
        issuer=settings.oidc_issuer_url,
        authorization_endpoint=f"{settings.oidc_issuer_url}/protocol/openid-connect/auth",
        token_endpoint=f"{settings.oidc_issuer_url}/protocol/openid-connect/token",
        jwks_uri=f"{settings.oidc_issuer_url}/protocol/openid-connect/certs",
        userinfo_endpoint=f"{settings.oidc_issuer_url}/protocol/openid-connect/userinfo",
        end_session_endpoint=f"{settings.oidc_issuer_url}/protocol/openid-connect/logout",
    )
    params = {
        "client_id": settings.oidc_client_id,
        "response_type": "code",
        "scope": "openid profile email",
        "redirect_uri": settings.oidc_redirect_uri,
        "state": state,
        "nonce": nonce,
        "code_challenge": create_pkce_challenge(state),
        "code_challenge_method": "S256",
    }
    return f"{oidc_config.authorization_endpoint}?{urlencode(params)}"


def create_pkce_challenge(verifier: str) -> str:
    import hashlib
    import base64
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


async def exchange_code_for_tokens(code: str, code_verifier: str) -> dict:
    oidc_config = await get_oidc_config()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            oidc_config.token_endpoint,
            data={
                "grant_type": "authorization_code",
                "client_id": settings.oidc_client_id,
                "client_secret": settings.oidc_client_secret,
                "code": code,
                "redirect_uri": settings.oidc_redirect_uri,
                "code_verifier": code_verifier,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()


async def get_userinfo(access_token: str) -> dict:
    oidc_config = await get_oidc_config()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            oidc_config.userinfo_endpoint,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes))
    to_encode.update({"exp": int(expire.timestamp()), "iat": int(now.timestamp())})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return TokenData(**payload)
    except JWTError:
        return None


def verify_csrf_token(csrf_token: str, stored_token: str) -> bool:
    return secrets.compare_digest(csrf_token, stored_token)


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def build_logout_url(id_token_hint: Optional[str] = None) -> str:
    oidc_config = OIDCConfig(
        issuer=settings.oidc_issuer_url,
        authorization_endpoint=f"{settings.oidc_issuer_url}/protocol/openid-connect/auth",
        token_endpoint=f"{settings.oidc_issuer_url}/protocol/openid-connect/token",
        jwks_uri=f"{settings.oidc_issuer_url}/protocol/openid-connect/certs",
        userinfo_endpoint=f"{settings.oidc_issuer_url}/protocol/openid-connect/userinfo",
        end_session_endpoint=f"{settings.oidc_issuer_url}/protocol/openid-connect/logout",
    )
    params = {
        "post_logout_redirect_uri": settings.oidc_logout_redirect_uri,
    }
    if id_token_hint:
        params["id_token_hint"] = id_token_hint
    return f"{oidc_config.end_session_endpoint}?{urlencode(params)}"