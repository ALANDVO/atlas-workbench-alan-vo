from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_db
from app.core.security import (
    create_state,
    create_nonce,
    build_authorization_url,
    exchange_code_for_tokens,
    get_userinfo,
    create_access_token,
    generate_csrf_token,
    verify_csrf_token,
    build_logout_url,
    decode_token,
    TokenData,
)
from app.core.config import get_settings
from app.models.user import User, UserRole
from app.models.audit import AuditLog
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

# In-memory state storage (use Redis in production)
_auth_states: dict[str, dict] = {}
_csrf_tokens: dict[str, str] = {}


@router.get("/login")
async def login(request: Request):
    state = create_state()
    nonce = create_nonce()
    _auth_states[state] = {"nonce": nonce, "pkce_verifier": state}

    auth_url = build_authorization_url(state, nonce)
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")

    if error:
        raise HTTPException(status_code=400, detail=f"OIDC error: {error}")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    stored = _auth_states.pop(state, None)
    if not stored:
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    try:
        tokens = await exchange_code_for_tokens(code, stored["pkce_verifier"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {e}")

    access_token = tokens.get("access_token")
    id_token = tokens.get("id_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="No access token received")

    try:
        userinfo = await get_userinfo(access_token)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Userinfo fetch failed: {e}")

    # Find or create user
    keycloak_id = userinfo.get("sub")
    email = userinfo.get("email")
    name = userinfo.get("name") or userinfo.get("preferred_username") or email

    if not keycloak_id or not email:
        raise HTTPException(status_code=400, detail="Invalid userinfo response")

    result = await db.execute(select(User).where(User.keycloak_id == keycloak_id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(keycloak_id=keycloak_id, email=email, name=name, roles="operator")
        db.add(user)
        await db.flush()
    else:
        user.email = email
        user.name = name

    # Map realm roles from token
    realm_access = tokens.get("realm_access", {})
    roles = realm_access.get("roles", [])
    if "admin" in roles:
        user.set_roles([UserRole.ADMIN])
    elif "analyst" in roles:
        user.set_roles([UserRole.ANALYST])
    else:
        user.set_roles([UserRole.OPERATOR])

    # Create JWT
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "name": user.name,
        "roles": [r.value for r in user.get_roles()],
    }
    jwt_token = create_access_token(token_data)

    # Set cookie
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.jwt_access_token_expire_minutes * 60,
        path="/",
    )

    # Create CSRF token
    csrf_token = generate_csrf_token()
    _csrf_tokens[str(user.id)] = csrf_token

    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action="login",
        resource_type="auth",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(audit)

    # Redirect to frontend
    return RedirectResponse(url=settings.oidc_logout_redirect_uri.replace("/auth/logout", ""))


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Get id_token_hint from token
    token = request.cookies.get("access_token")
    id_token_hint = None
    if token:
        token_data = decode_token(token)
        if token_data:
            id_token_hint = token_data.sub

    # Clear cookies
    response.delete_cookie("access_token", path="/", httponly=True, secure=settings.cookie_secure, samesite=settings.cookie_samesite)
    response.delete_cookie("csrf_token", path="/", httponly=True, secure=settings.cookie_secure, samesite=settings.cookie_samesite)

    # Remove CSRF token
    _csrf_tokens.pop(str(user.id), None)

    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action="logout",
        resource_type="auth",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(audit)

    logout_url = build_logout_url(id_token_hint)
    return {"logout_url": logout_url}


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {
        "authenticated": True,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "roles": [r.value for r in user.get_roles()],
        },
    }


@router.get("/csrf")
async def get_csrf(user: User = Depends(get_current_user)):
    csrf_token = _csrf_tokens.get(str(user.id))
    if not csrf_token:
        csrf_token = generate_csrf_token()
        _csrf_tokens[str(user.id)] = csrf_token
    return {"csrf_token": csrf_token}


@router.post("/verify-csrf")
async def verify_csrf(
    request: Request,
    user: User = Depends(get_current_user),
):
    body = await request.json()
    csrf_token = body.get("csrf_token")
    if not csrf_token:
        raise HTTPException(status_code=400, detail="CSRF token required")

    stored = _csrf_tokens.get(str(user.id))
    if not stored or not verify_csrf_token(csrf_token, stored):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    return {"valid": True}