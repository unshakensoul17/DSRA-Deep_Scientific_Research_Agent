"""
DSRA V2 — Research Sessions & Reports Router
=============================================
Endpoints for managing research session creation, listing, status checks,
running agent workflows as background tasks, and streaming SSE progress logs.
"""

import json
from typing import Any, Optional
import uuid
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.events import event_broker
from app.core.orchestrator import ResearchOrchestrator
from app.db.models.report import Report
from app.db.models.research_session import ResearchSession
from app.db.models.user import User
from app.db.repositories.report import ReportRepository
from app.db.repositories.research_session import ResearchSessionRepository
from app.db.session import get_db_session
from app.schemas.api.reports import ReportListItemResponse, ReportResponse
from app.schemas.api.research import (
    ResearchSessionCreateRequest,
    ResearchSessionDetailResponse,
    ResearchSessionResponse,
    ResearchSessionStartResponse,
)
from app.schemas.common import SessionState, ReportStatus

router = APIRouter(tags=["Research Workspaces"])


@router.post("/sessions", response_model=ResearchSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: ResearchSessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Any:
    """
    Create a new research workspace session owned by the authenticated user.
    """
    session_repo = ResearchSessionRepository(db)
    
    from datetime import datetime, timezone
    new_session = ResearchSession(
        id=uuid.uuid4(),
        user_id=current_user.id,
        topic=request.topic,
        state=SessionState.CREATED,
        depth=request.depth,
        max_iterations=request.max_iterations,
        iteration_count=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    await session_repo.create(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    return ResearchSessionResponse(
        session_id=new_session.id,
        topic=new_session.topic,
        state=new_session.state,
        depth=new_session.depth,
        iteration_count=new_session.iteration_count,
        max_iterations=new_session.max_iterations,
        created_at=new_session.created_at,
        updated_at=new_session.updated_at,
        completed_at=new_session.completed_at
    )


@router.get("/sessions", response_model=list[ResearchSessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Any:
    """
    List all research sessions belonging to the current authenticated user.
    """
    query = (
        select(ResearchSession)
        .where(ResearchSession.user_id == current_user.id)
        .order_by(ResearchSession.created_at.desc())
    )
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    return [
        ResearchSessionResponse(
            session_id=s.id,
            topic=s.topic,
            state=s.state,
            depth=s.depth,
            iteration_count=s.iteration_count,
            max_iterations=s.max_iterations,
            created_at=s.created_at,
            updated_at=s.updated_at,
            completed_at=s.completed_at
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}", response_model=ResearchSessionDetailResponse)
async def get_session_details(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Any:
    """
    Fetch comprehensive details, source metrics, and timeline state of a specific session.
    """
    session_repo = ResearchSessionRepository(db)
    session = await session_repo.get_by_id_with_relationships(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research session not found."
        )
        
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden to this research workspace."
        )

    # Compile counts
    sources_count = len(session.sources)
    claims_count = len(session.claims)
    verified_claims_count = sum(1 for c in session.claims if c.verification_status == "VERIFIED")
    
    # Get active report if finalized
    report_id = None
    if session.reports:
        # Get the latest report
        latest_report = sorted(session.reports, key=lambda r: r.created_at, reverse=True)[0]
        report_id = latest_report.id

    # Format timeline execution log history
    agent_timeline = [
        {
            "agent": log.agent,
            "status": log.status,
            "message": log.message,
            "timestamp": log.created_at.isoformat() if log.created_at else None
        }
        for log in sorted(session.execution_logs, key=lambda l: l.created_at)
    ]

    return ResearchSessionDetailResponse(
        session_id=session.id,
        topic=session.topic,
        state=session.state,
        depth=session.depth,
        iteration_count=session.iteration_count,
        max_iterations=session.max_iterations,
        created_at=session.created_at,
        updated_at=session.updated_at,
        completed_at=session.completed_at,
        sources_count=sources_count,
        claims_count=claims_count,
        verified_claims_count=verified_claims_count,
        report_id=report_id,
        agent_timeline=agent_timeline
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Delete a research session and all associated database records (cascade).
    """
    session_repo = ResearchSessionRepository(db)
    session = await session_repo.get_by_id(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research session not found."
        )
        
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden."
        )

    await session_repo.delete(session_id)
    await db.commit()


async def _run_orchestrator_job(session_id: UUID) -> None:
    """Helper job to spin up orchestrator with a dedicated DB session connection."""
    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        try:
            orchestrator = ResearchOrchestrator(session)
            await orchestrator.run_research_session(session_id)
        except Exception as e:
            # The orchestrator handles internal exceptions, but log anyway in case of engine errors
            import structlog
            structlog.get_logger(__name__).error("background_orchestrator_failed", error=str(e), session_id=str(session_id))


@router.post("/sessions/{session_id}/start", response_model=ResearchSessionStartResponse)
async def start_session_execution(
    session_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Any:
    """
    Spawn the background research worker threads for a created session.
    """
    session_repo = ResearchSessionRepository(db)
    session = await session_repo.get_by_id(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research session not found."
        )
        
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden."
        )
        
    if session.state not in [SessionState.CREATED, SessionState.ERROR, SessionState.COMPLETED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start session in state {session.state}."
        )

    # Queue background task
    background_tasks.add_task(_run_orchestrator_job, session_id)
    
    # Return starting payload
    return ResearchSessionStartResponse(
        session_id=session_id,
        state=SessionState.PLANNING,
        stream_url=f"/api/v1/sessions/{session_id}/stream"
    )


@router.get("/sessions/{session_id}/stream")
async def stream_session_progress(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    """
    Server-Sent Events (SSE) streaming channel returning real-time agent checkpoints.
    """
    session_repo = ResearchSessionRepository(db)
    session = await session_repo.get_by_id(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research session not found."
        )
        
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden."
        )

    async def event_generator():
        try:
            async for sse_event in event_broker.subscribe(session_id):
                # Standard SSE block formatting
                # Event lines separated by newlines
                yield f"event: {sse_event.event.value}\n"
                yield f"data: {json.dumps(sse_event.data)}\n\n"
        except Exception as e:
            # Yield error event and abort
            yield f"event: error\n"
            yield f"data: {json.dumps({'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ── Reports Endpoints ──────────────────────────────────────────────────

@router.get("/reports", response_model=list[ReportListItemResponse])
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Any:
    """
    List all compiled research report drafts for the current user.
    """
    query = (
        select(Report)
        .join(ResearchSession)
        .where(ResearchSession.user_id == current_user.id)
        .order_by(Report.created_at.desc())
    )
    result = await db.execute(query)
    reports = result.scalars().all()
    
    return [
        ReportListItemResponse(
            id=r.id,
            session_id=r.session_id,
            title=r.title,
            executive_summary_snippet=r.executive_summary[:200] + "...",
            status=ReportStatus(r.status),
            critique_score=r.critique_score,
            created_at=r.created_at
        )
        for r in reports
    ]


@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report_details(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Any:
    """
    Fetch the complete structured report draft matching report_id.
    """
    report_repo = ReportRepository(db)
    report = await report_repo.get_by_id(report_id)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found."
        )

    # Check ownership by loading the associated session
    query = select(ResearchSession).where(ResearchSession.id == report.session_id)
    res = await db.execute(query)
    session = res.scalar_one_or_none()
    
    if not session or session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden to this report."
        )

    # Convert database structured JSON fields to lists/schemas expected by response model
    # SQLAlchemy columns sections and references are JSON fields
    return ReportResponse(
        id=report.id,
        session_id=report.session_id,
        title=report.title,
        executive_summary=report.executive_summary,
        sections=report.sections,
        key_findings=report.key_findings,
        references=report.references,
        critique_score=report.critique_score,
        status=ReportStatus(report.status),
        export_paths=report.export_paths or {},
        created_at=report.created_at,
        finalized_at=report.finalized_at
    )
