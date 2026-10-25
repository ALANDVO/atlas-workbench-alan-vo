from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.session import CompressionSession, CompressionMode
from app.models.request import CompressionRequest
from app.models.audit import AuditLog

router = APIRouter(prefix="/compression", tags=["compression"])


def session_to_dict(session: CompressionSession) -> dict:
    return {
        "id": str(session.id),
        "session_name": session.session_name,
        "mode": session.mode.value,
        "provider": session.provider,
        "model": session.model,
        "base_url": session.base_url,
        "total_requests": session.total_requests,
        "eligible_requests": session.eligible_requests,
        "tokens_before": session.tokens_before,
        "tokens_after": session.tokens_after,
        "tokens_saved": session.tokens_saved,
        "savings_ratio": session.savings_ratio_float,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
    }


def request_to_dict(req: CompressionRequest) -> dict:
    return {
        "id": str(req.id),
        "session_id": str(req.session_id),
        "provider": req.provider,
        "model": req.model,
        "mode": req.mode.value,
        "input_tokens": req.input_tokens,
        "output_tokens": req.output_tokens,
        "compressed_tokens": req.compressed_tokens,
        "recovered_tokens": req.recovered_tokens,
        "savings": req.savings,
        "mcp_recovery_used": req.mcp_recovery_used,
        "duration_ms": req.duration_ms,
        "status": req.status,
        "error_message": req.error_message,
        "created_at": req.created_at.isoformat(),
    }


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_session(
    data: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session_name = data.get("session_name")
    mode = data.get("mode")
    provider = data.get("provider")
    model = data.get("model")
    base_url = data.get("base_url")

    if not all([session_name, mode, provider, model]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    try:
        mode_enum = CompressionMode(mode)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid mode")

    session = CompressionSession(
        user_id=user.id,
        session_name=session_name,
        mode=mode_enum,
        provider=provider,
        model=model,
        base_url=base_url,
    )
    db.add(session)

    audit = AuditLog(
        user_id=user.id,
        action="create_session",
        resource_type="compression_session",
        resource_id=str(session.id),
        details=f"Created session '{session_name}' with mode {mode}",
    )
    db.add(audit)

    await db.flush()
    await db.refresh(session)
    return session_to_dict(session)


@router.get("/sessions")
async def list_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    mode: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    query = select(CompressionSession).where(CompressionSession.user_id == user.id)

    if mode:
        try:
            mode_enum = CompressionMode(mode)
            query = query.where(CompressionSession.mode == mode_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid mode")

    if status == "active":
        query = query.where(CompressionSession.ended_at.is_(None))
    elif status == "ended":
        query = query.where(CompressionSession.ended_at.is_not(None))

    query = query.order_by(desc(CompressionSession.created_at))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    sessions = result.scalars().all()

    return {
        "items": [session_to_dict(s) for s in sessions],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CompressionSession)
        .where(CompressionSession.id == session_id)
        .where(CompressionSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_to_dict(session)


@router.patch("/sessions/{session_id}")
async def update_session(
    session_id: UUID,
    data: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CompressionSession)
        .where(CompressionSession.id == session_id)
        .where(CompressionSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.ended_at:
        raise HTTPException(status_code=400, detail="Cannot update ended session")

    if "session_name" in data:
        session.session_name = data["session_name"]
    if "mode" in data:
        try:
            session.mode = CompressionMode(data["mode"])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid mode")

    session.updated_at = datetime.now(timezone.utc)

    audit = AuditLog(
        user_id=user.id,
        action="update_session",
        resource_type="compression_session",
        resource_id=str(session.id),
        details=f"Updated session",
    )
    db.add(audit)

    await db.flush()
    return session_to_dict(session)


@router.post("/sessions/{session_id}/end")
async def end_session(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CompressionSession)
        .where(CompressionSession.id == session_id)
        .where(CompressionSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.ended_at:
        raise HTTPException(status_code=400, detail="Session already ended")

    session.ended_at = datetime.now(timezone.utc)
    session.updated_at = datetime.now(timezone.utc)

    audit = AuditLog(
        user_id=user.id,
        action="end_session",
        resource_type="compression_session",
        resource_id=str(session.id),
        details=f"Ended session",
    )
    db.add(audit)

    await db.flush()
    return session_to_dict(session)


@router.get("/sessions/{session_id}/requests")
async def list_session_requests(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    # Verify session ownership
    result = await db.execute(
        select(CompressionSession.id)
        .where(CompressionSession.id == session_id)
        .where(CompressionSession.user_id == user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Session not found")

    query = select(CompressionRequest).where(CompressionRequest.session_id == session_id)
    query = query.order_by(desc(CompressionRequest.created_at))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    requests = result.scalars().all()

    return {
        "items": [request_to_dict(r) for r in requests],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/stats/summary")
async def get_stats_summary(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Aggregate stats for user's sessions
    result = await db.execute(
        select(
            func.count(CompressionSession.id),
            func.sum(CompressionSession.total_requests),
            func.sum(CompressionSession.eligible_requests),
            func.sum(CompressionSession.tokens_before),
            func.sum(CompressionSession.tokens_after),
            func.sum(CompressionSession.tokens_saved),
        ).where(CompressionSession.user_id == user.id)
    )
    row = result.one()
    total_sessions = row[0] or 0
    total_requests = row[1] or 0
    eligible_requests = row[2] or 0
    tokens_before = row[3] or 0
    tokens_after = row[4] or 0
    tokens_saved = row[5] or 0

    eligibility_rate = eligible_requests / total_requests if total_requests > 0 else 0
    overall_savings_ratio = tokens_saved / tokens_before if tokens_before > 0 else 0

    return {
        "total_sessions": total_sessions,
        "total_requests": total_requests,
        "eligible_requests": eligible_requests,
        "eligibility_rate": eligibility_rate,
        "tokens_before": tokens_before,
        "tokens_after": tokens_after,
        "tokens_saved": tokens_saved,
        "overall_savings_ratio": overall_savings_ratio,
    }