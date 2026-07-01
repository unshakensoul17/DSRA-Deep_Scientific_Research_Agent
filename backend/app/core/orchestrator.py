"""
DSRA V2 — Research Orchestration Engine
=========================================
Coordinates the multi-agent DAG workflow, database transaction updates,
and real-time event broadcasting.
"""

import asyncio
from datetime import datetime
import traceback
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.events import event_broker
from app.core.logging import get_logger
from app.core.state import StateMachine
from app.db.models.agent_log import AgentExecutionLog
from app.db.models.research_query import ResearchQuery
from app.db.models.source import Source as DBSource
from app.db.models.claim import Claim as DBClaim, VerificationResult as DBVerificationResult
from app.db.models.report import Report as DBReport
from app.db.repositories.research_session import ResearchSessionRepository
from app.db.repositories.source import SourceRepository
from app.db.repositories.claim import ClaimRepository
from app.db.repositories.report import ReportRepository
from app.exceptions.base import DSRABaseError, AgentExecutionError
from app.schemas.common import (
    ResearchDepth,
    SessionState,
    SourceResult,
    SourceType,
    SSEEvent,
    SSEEventType,
    VerifiedClaim,
)

log = get_logger(__name__)
settings = get_settings()


class ResearchOrchestrator:
    """
    Core orchestrator that runs the iterative research agent loop.
    Ensures safe database operations and non-blocking event emissions.
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.session_repo = ResearchSessionRepository(db_session)
        self.source_repo = SourceRepository(db_session)
        self.claim_repo = ClaimRepository(db_session)
        self.report_repo = ReportRepository(db_session)

    async def run_research_session(self, session_id: UUID) -> None:
        """
        Executes the entire research DAG for a session from start to finish.
        Designed to run as a background task.
        """
        log.info("research_session_execution_started", session_id=str(session_id))
        
        try:
            # 1. Transition state to PLANNING
            session = await self._transition_state(session_id, SessionState.CREATED, SessionState.PLANNING)
            
            # --- PLANNING PHASE ---
            log.info("planning_phase_started", session_id=str(session_id))
            plan = await self._run_planner_agent(session)
            
            # Save generated queries to database
            queries_created = []
            for q in plan.queries:
                db_q = ResearchQuery(
                    session_id=session_id,
                    query_text=q.query_text,
                    source_type=q.source_type,
                    iteration=0,
                    filters=q.filters
                )
                self.db_session.add(db_q)
                queries_created.append(db_q)
            await self.db_session.commit()
            
            # --- RESEARCH ITERATIVE LOOP ---
            iteration = 0
            max_iter = session.max_iterations or settings.default_max_iterations
            all_sources: list[SourceResult] = []
            verified_claims: list[VerifiedClaim] = []
            
            # Prepare current active queries
            current_queries = plan.queries
            
            while iteration < max_iter:
                # Update iteration count in DB
                session.iteration_count = iteration
                await self.db_session.commit()
                
                # 2. Transition state to RETRIEVAL
                await self._transition_state(session_id, session.state, SessionState.RETRIEVAL)
                
                # Run parallel retrievers
                log.info("retrieval_phase_started", session_id=str(session_id), iteration=iteration)
                new_sources = await self._run_retrieval_agents(session_id, current_queries)
                all_sources.extend(new_sources)
                
                # Publish source count update to SSE
                await event_broker.publish(
                    session_id,
                    SSEEvent(
                        event=SSEEventType.SOURCE_BATCH_FETCHED,
                        session_id=session_id,
                        data={"count": len(new_sources), "total_so_far": len(all_sources)}
                    )
                )
                
                # 3. Transition state to EVIDENCE_EXTRACTION
                await self._transition_state(session_id, SessionState.RETRIEVAL, SessionState.EVIDENCE_EXTRACTION)
                log.info("evidence_phase_started", session_id=str(session_id), iteration=iteration)
                
                evidence_pieces, source_qualities = await self._run_evidence_agent(session_id, new_sources, session.topic)
                
                # Update source quality scores in DB
                for db_source in session.sources:
                    score = source_qualities.get(str(db_source.id))
                    if score is not None:
                        db_source.quality_score = score
                await self.db_session.commit()
                
                # Emit evidence count to SSE
                await event_broker.publish(
                    session_id,
                    SSEEvent(
                        event=SSEEventType.EVIDENCE_EXTRACTED,
                        session_id=session_id,
                        data={"evidence_count": len(evidence_pieces)}
                    )
                )
                
                # 4. Transition state to VERIFICATION
                await self._transition_state(session_id, SessionState.EVIDENCE_EXTRACTION, SessionState.VERIFICATION)
                log.info("verification_phase_started", session_id=str(session_id), iteration=iteration)
                
                new_verified_claims = await self._run_verification_agent(session_id, evidence_pieces, all_sources, session.topic)
                verified_claims.extend(new_verified_claims)
                
                # 5. Transition state to GAP_ANALYSIS
                await self._transition_state(session_id, SessionState.VERIFICATION, SessionState.GAP_ANALYSIS)
                log.info("gap_analysis_phase_started", session_id=str(session_id), iteration=iteration)
                
                gap_report = await self._run_gap_analysis_agent(
                    session_id, plan, verified_claims, len(all_sources), iteration, max_iter
                )
                
                # Emit gaps info to SSE
                await event_broker.publish(
                    session_id,
                    SSEEvent(
                        event=SSEEventType.GAP_DETECTED,
                        session_id=session_id,
                        data={
                            "gaps": [g.description for g in gap_report.gaps],
                            "will_iterate": gap_report.should_iterate,
                            "iteration": iteration + 1
                        }
                    )
                )
                
                if gap_report.should_iterate and iteration + 1 < max_iter:
                    # Save new gap-filling queries to DB
                    for q in gap_report.new_queries:
                        db_q = ResearchQuery(
                            session_id=session_id,
                            query_text=q.query_text,
                            source_type=q.source_type,
                            iteration=iteration + 1,
                            filters=q.filters
                        )
                        self.db_session.add(db_q)
                    await self.db_session.commit()
                    
                    current_queries = gap_report.new_queries
                    iteration += 1
                    
                    # Transition state to ITERATING
                    await self._transition_state(session_id, SessionState.GAP_ANALYSIS, SessionState.ITERATING)
                    await asyncio.sleep(0.5)  # Let connection settle
                else:
                    break
            
            # --- WRITING & CRITIQUE PHASE ---
            revision = 0
            max_rev = settings.default_max_revisions
            critique = None
            draft = None
            
            while revision <= max_rev:
                # Transition state to WRITING
                current_state = session.state
                await self._transition_state(session_id, current_state, SessionState.WRITING)
                log.info("writing_phase_started", session_id=str(session_id), revision=revision)
                
                draft = await self._run_writer_agent(session_id, plan, verified_claims, all_sources, draft, critique)
                
                # Emit sections info to SSE
                for idx, sect in enumerate(draft.sections):
                    await event_broker.publish(
                        session_id,
                        SSEEvent(
                            event=SSEEventType.REPORT_SECTION_COMPLETE,
                            session_id=session_id,
                            data={"section": sect.title, "word_count": sect.word_count, "index": idx}
                        )
                    )
                
                # Transition state to CRITIQUE
                await self._transition_state(session_id, SessionState.WRITING, SessionState.CRITIQUE)
                log.info("critique_phase_started", session_id=str(session_id), revision=revision)
                
                critique = await self._run_critic_agent(session_id, draft, verified_claims, all_sources, revision, max_rev)
                
                if critique.revision_required and revision < max_rev:
                    revision += 1
                else:
                    break
            
            # --- VISUALIZATION PHASE ---
            await self._transition_state(session_id, SessionState.CRITIQUE, SessionState.VISUALIZATION)
            log.info("visualization_phase_started", session_id=str(session_id))
            viz_bundle = await self._run_visualization_agent(session_id, draft, verified_claims, all_sources)
            
            # --- EXPORT PHASE ---
            await self._transition_state(session_id, SessionState.VISUALIZATION, SessionState.EXPORT)
            log.info("export_phase_started", session_id=str(session_id))
            export_bundle = await self._run_export_agent(session_id, draft, viz_bundle, all_sources)
            
            # --- FINALIZATION ---
            # Save final report to DB
            db_report = DBReport(
                session_id=session_id,
                title=draft.title,
                executive_summary=draft.executive_summary,
                sections=[s.model_dump() for s in draft.sections],
                key_findings=draft.key_findings,
                methodology=draft.methodology_description,
                limitations=draft.limitations,
                conclusion=draft.conclusion,
                references=[r.model_dump() for r in draft.references],
                status=draft.status,
                critique_score=critique.overall_score,
                export_paths={
                    "pdf": export_bundle.pdf_path or "",
                    "markdown": export_bundle.markdown_path or "",
                    "html": export_bundle.html_path or "",
                    "json": export_bundle.json_path or "",
                },
                finalized_at=datetime.utcnow()
            )
            self.db_session.add(db_report)
            
            session.completed_at = datetime.utcnow()
            await self._transition_state(session_id, SessionState.EXPORT, SessionState.COMPLETED)
            await self.db_session.commit()
            
            # Publish completion event
            await event_broker.publish(
                session_id,
                SSEEvent(
                    event=SSEEventType.RESEARCH_COMPLETE,
                    session_id=session_id,
                    data={"report_id": str(db_report.id)}
                )
            )
            log.info("research_session_execution_completed", session_id=str(session_id), report_id=str(db_report.id))
            
        except Exception as e:
            # Handle failure
            stack = traceback.format_exc()
            log.error("research_session_execution_failed", session_id=str(session_id), error=str(e), traceback=stack)
            await self.db_session.rollback()
            
            try:
                # Attempt to transition to FAILED state safely
                session = await self.session_repo.get_by_id(session_id)
                if session and session.state not in SessionState.terminal_states():
                    session.state = SessionState.FAILED
                    session.completed_at = datetime.utcnow()
                    await self.db_session.commit()
            except Exception as inner_e:
                log.critical("failed_setting_failed_state", session_id=str(session_id), error=str(inner_e))
                
            # Publish error event to subscribers
            await event_broker.publish(
                session_id,
                SSEEvent(
                    event=SSEEventType.ERROR,
                    session_id=session_id,
                    data={"message": str(e), "code": getattr(e, "code", "INTERNAL_ERROR")}
                )
            )

    async def _transition_state(
        self, session_id: UUID, current: SessionState, target: SessionState
    ) -> "ResearchSession":
        """Validate, transition DB state, commit, and emit state_changed SSE event."""
        StateMachine.validate_transition(current, target)
        
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise RuntimeError(f"Session {session_id} not found during state transition.")
            
        session.state = target
        session.updated_at = datetime.utcnow()
        await self.db_session.commit()
        
        # Publish SSE update
        await event_broker.publish(
            session_id,
            SSEEvent(
                event=SSEEventType.SESSION_STATE_CHANGED,
                session_id=session_id,
                data={"state": target.value}
            )
        )
        return session

    # ── Agent Runners (Dynamic Import & Execution Wrapper) ───────────────────

    async def _run_planner_agent(self, session) -> Any:
        """Dynamic import and execute PlannerAgent."""
        from app.agents.planner import PlannerAgent
        from app.schemas.agents.planner import ResearchGoal
        
        # Track start time for logging audit
        start_t = datetime.utcnow()
        
        goal = ResearchGoal(
            session_id=session.id,
            topic=session.topic,
            depth=session.depth,
            max_sources_per_query=getattr(session, "max_sources_per_query", settings.default_max_sources_per_query),
            source_preferences=[SourceType(pref) for pref in session.source_preferences] if getattr(session, "source_preferences", None) else list(SourceType),
            focus_areas=getattr(session, "focus_areas", None) or []
        )
        
        agent = PlannerAgent()
        await event_broker.publish(session.id, SSEEvent(event=SSEEventType.AGENT_STARTED, session_id=session.id, data={"agent": agent.name}))
        
        try:
            plan = await agent.run(goal)
            duration = int((datetime.utcnow() - start_t).total_seconds() * 1000)
            
            # Log execution metrics to DB
            audit_log = AgentExecutionLog(
                session_id=session.id,
                agent_name=agent.name,
                state_entered=SessionState.PLANNING.value,
                duration_ms=duration,
                metadata_json={"estimated_complexity": plan.estimated_complexity}
            )
            self.db_session.add(audit_log)
            
            await event_broker.publish(session.id, SSEEvent(event=SSEEventType.AGENT_COMPLETED, session_id=session.id, data={"agent": agent.name, "duration_ms": duration}))
            return plan
        except Exception as e:
            duration = int((datetime.utcnow() - start_t).total_seconds() * 1000)
            audit_log = AgentExecutionLog(
                session_id=session.id,
                agent_name=agent.name,
                state_entered=SessionState.PLANNING.value,
                duration_ms=duration,
                error_message=str(e)
            )
            self.db_session.add(audit_log)
            await event_broker.publish(session.id, SSEEvent(event=SSEEventType.AGENT_FAILED, session_id=session.id, data={"agent": agent.name, "error": str(e)}))
            raise AgentExecutionError(message=f"Planner agent failed: {str(e)}") from e

    async def _run_retrieval_agents(self, session_id: UUID, queries: list) -> list[SourceResult]:
        """Runs research queries in parallel across source retrievers."""
        from app.agents.researcher import ResearchAgent
        from app.schemas.agents.all_agents import ResearchAgentInput
        
        start_t = datetime.utcnow()
        agent = ResearchAgent()
        await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_STARTED, session_id=session_id, data={"agent": agent.name}))
        
        async def fetch_one(query_item) -> list[SourceResult]:
            agent_input = ResearchAgentInput(
                session_id=session_id,
                query=query_item,
                max_results=settings.default_max_sources_per_query
            )
            output = await agent.run(agent_input)
            
            # Save raw sources to database
            for src in output.results:
                db_source = DBSource(
                    session_id=session_id,
                    query_id=query_item.id,
                    title=src.title,
                    url=str(src.url) if src.url else None,
                    snippet=src.snippet,
                    full_content=src.full_content,
                    source_type=src.source_type,
                    authors=src.authors,
                    year=src.year,
                    doi=src.doi,
                    citation_count=src.citation_count
                )
                self.db_session.add(db_source)
            return output.results

        try:
            # Parallel execution using asyncio.gather
            tasks = [fetch_one(q) for q in queries]
            results_batches = await asyncio.gather(*tasks)
            await self.db_session.commit()
            
            # Flatten results list
            all_sources = [src for batch in results_batches for src in batch]
            duration = int((datetime.utcnow() - start_t).total_seconds() * 1000)
            
            audit_log = AgentExecutionLog(
                session_id=session_id,
                agent_name=agent.name,
                state_entered=SessionState.RETRIEVAL.value,
                duration_ms=duration,
                metadata_json={"queries_count": len(queries), "sources_fetched": len(all_sources)}
            )
            self.db_session.add(audit_log)
            
            await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_COMPLETED, session_id=session_id, data={"agent": agent.name, "duration_ms": duration}))
            return all_sources
        except Exception as e:
            duration = int((datetime.utcnow() - start_t).total_seconds() * 1000)
            audit_log = AgentExecutionLog(
                session_id=session_id,
                agent_name=agent.name,
                state_entered=SessionState.RETRIEVAL.value,
                duration_ms=duration,
                error_message=str(e)
            )
            self.db_session.add(audit_log)
            await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_FAILED, session_id=session_id, data={"agent": agent.name, "error": str(e)}))
            raise AgentExecutionError(message=f"Retrieval agent failed: {str(e)}") from e

    async def _run_evidence_agent(self, session_id: UUID, sources: list[SourceResult], topic: str) -> tuple[list, dict[str, float]]:
        """Extract evidence pieces from retrieved sources."""
        from app.agents.evidence import EvidenceAgent
        from app.schemas.agents.all_agents import EvidenceAgentInput
        
        start_t = datetime.utcnow()
        agent = EvidenceAgent()
        await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_STARTED, session_id=session_id, data={"agent": agent.name}))
        
        agent_input = EvidenceAgentInput(
            session_id=session_id,
            sources=sources,
            research_topic=topic
        )
        
        try:
            output = await agent.run(agent_input)
            duration = int((datetime.utcnow() - start_t).total_seconds() * 1000)
            
            # Save extracted claims to DB as UNVERIFIED
            for ep in output.evidence_pieces:
                db_claim = DBClaim(
                    session_id=session_id,
                    text=ep.claim_text,
                    confidence=0.0,
                    status=SessionState.CREATED.value,  # Placeholder state
                    source_ids=[ep.source_id],
                    iteration=ep.iteration
                )
                self.db_session.add(db_claim)
            await self.db_session.commit()
            
            audit_log = AgentExecutionLog(
                session_id=session_id,
                agent_name=agent.name,
                state_entered=SessionState.EVIDENCE_EXTRACTION.value,
                duration_ms=duration,
                metadata_json={"evidence_extracted": len(output.evidence_pieces)}
            )
            self.db_session.add(audit_log)
            
            await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_COMPLETED, session_id=session_id, data={"agent": agent.name, "duration_ms": duration}))
            return output.evidence_pieces, output.source_quality_scores
        except Exception as e:
            duration = int((datetime.utcnow() - start_t).total_seconds() * 1000)
            audit_log = AgentExecutionLog(
                session_id=session_id,
                agent_name=agent.name,
                state_entered=SessionState.EVIDENCE_EXTRACTION.value,
                duration_ms=duration,
                error_message=str(e)
            )
            self.db_session.add(audit_log)
            await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_FAILED, session_id=session_id, data={"agent": agent.name, "error": str(e)}))
            raise AgentExecutionError(message=f"Evidence agent failed: {str(e)}") from e

    async def _run_verification_agent(self, session_id: UUID, evidence: list, sources: list[SourceResult], topic: str) -> list[VerifiedClaim]:
        """Cross-reference claims to assign verification status."""
        from app.agents.verification import VerificationAgent
        from app.schemas.agents.all_agents import VerificationAgentInput
        
        start_t = datetime.utcnow()
        agent = VerificationAgent()
        await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_STARTED, session_id=session_id, data={"agent": agent.name}))
        
        agent_input = VerificationAgentInput(
            session_id=session_id,
            evidence_pieces=evidence,
            sources=sources,
            research_topic=topic
        )
        
        try:
            output = await agent.run(agent_input)
            duration = int((datetime.utcnow() - start_t).total_seconds() * 1000)
            
            # Update DB claims with verification statuses and reasoning
            for vc in output.verified_claims:
                # Find matching unverified claim or insert
                # In normal execution, update corresponding DBClaim records
                # Let's insert VerificationResult logs
                for src_id in vc.supporting_source_ids:
                    db_res = DBVerificationResult(
                        claim_id=vc.id,  # Assume matching ID mapping
                        supporting_source_ids=vc.supporting_source_ids,
                        contradicting_source_ids=vc.contradicting_source_ids,
                        confidence=vc.confidence,
                        reasoning=vc.reasoning
                    )
                    self.db_session.add(db_res)
            await self.db_session.commit()
            
            audit_log = AgentExecutionLog(
                session_id=session_id,
                agent_name=agent.name,
                state_entered=SessionState.VERIFICATION.value,
                duration_ms=duration,
                metadata_json={"contradictions_found": output.contradictions_found}
            )
            self.db_session.add(audit_log)
            
            await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_COMPLETED, session_id=session_id, data={"agent": agent.name, "duration_ms": duration}))
            return output.verified_claims
        except Exception as e:
            duration = int((datetime.utcnow() - start_t).total_seconds() * 1000)
            audit_log = AgentExecutionLog(
                session_id=session_id,
                agent_name=agent.name,
                state_entered=SessionState.VERIFICATION.value,
                duration_ms=duration,
                error_message=str(e)
            )
            self.db_session.add(audit_log)
            await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_FAILED, session_id=session_id, data={"agent": agent.name, "error": str(e)}))
            raise AgentExecutionError(message=f"Verification agent failed: {str(e)}") from e

    async def _run_gap_analysis_agent(self, session_id: UUID, plan, claims: list, sources_count: int, iteration: int, max_iter: int) -> Any:
        """Check for research plan coverage gaps."""
        from app.agents.gap_analysis import GapAnalysisAgent
        from app.schemas.agents.all_agents import GapAnalysisAgentInput
        
        start_t = datetime.utcnow()
        agent = GapAnalysisAgent()
        await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_STARTED, session_id=session_id, data={"agent": agent.name}))
        
        agent_input = GapAnalysisAgentInput(
            session_id=session_id,
            research_plan_topic=plan.topic,
            research_plan_focus_areas=plan.focus_areas,
            verified_claims=claims,
            sources_count=sources_count,
            current_iteration=iteration,
            max_iterations=max_iter
        )
        
        try:
            output = await agent.run(agent_input)
            duration = int((datetime.utcnow() - start_t).total_seconds() * 1000)
            
            audit_log = AgentExecutionLog(
                session_id=session_id,
                agent_name=agent.name,
                state_entered=SessionState.GAP_ANALYSIS.value,
                duration_ms=duration,
                metadata_json={"gaps_count": len(output.gaps), "should_iterate": output.should_iterate}
            )
            self.db_session.add(audit_log)
            
            await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_COMPLETED, session_id=session_id, data={"agent": agent.name, "duration_ms": duration}))
            return output
        except Exception as e:
            duration = int((datetime.utcnow() - start_t).total_seconds() * 1000)
            audit_log = AgentExecutionLog(
                session_id=session_id,
                agent_name=agent.name,
                state_entered=SessionState.GAP_ANALYSIS.value,
                duration_ms=duration,
                error_message=str(e)
            )
            self.db_session.add(audit_log)
            await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_FAILED, session_id=session_id, data={"agent": agent.name, "error": str(e)}))
            raise AgentExecutionError(message=f"Gap analysis agent failed: {str(e)}") from e

    async def _run_writer_agent(self, session_id: UUID, plan, claims: list, sources: list, previous_draft=None, critique=None) -> Any:
        """Produce structured markdown sections draft."""
        from app.agents.writer import WriterAgent
        from app.schemas.agents.all_agents import WriterAgentInput
        
        start_t = datetime.utcnow()
        agent = WriterAgent()
        await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_STARTED, session_id=session_id, data={"agent": agent.name}))
        
        agent_input = WriterAgentInput(
            session_id=session_id,
            research_plan_topic=plan.topic,
            research_plan_focus_areas=plan.focus_areas,
            verified_claims=claims,
            sources=sources,
            previous_draft=previous_draft,
            critique=critique
        )
        
        try:
            output = await agent.run(agent_input)
            duration = int((datetime.utcnow() - start_t).total_seconds() * 1000)
            
            audit_log = AgentExecutionLog(
                session_id=session_id,
                agent_name=agent.name,
                state_entered=SessionState.WRITING.value,
                duration_ms=duration,
                metadata_json={"report_title": output.title}
            )
            self.db_session.add(audit_log)
            
            await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_COMPLETED, session_id=session_id, data={"agent": agent.name, "duration_ms": duration}))
            return output
        except Exception as e:
            duration = int((datetime.utcnow() - start_t).total_seconds() * 1000)
            audit_log = AgentExecutionLog(
                session_id=session_id,
                agent_name=agent.name,
                state_entered=SessionState.WRITING.value,
                duration_ms=duration,
                error_message=str(e)
            )
            self.db_session.add(audit_log)
            await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_FAILED, session_id=session_id, data={"agent": agent.name, "error": str(e)}))
            raise AgentExecutionError(message=f"Writer agent failed: {str(e)}") from e

    async def _run_critic_agent(self, session_id: UUID, draft, claims: list, sources: list, revision: int, max_rev: int) -> Any:
        """Critic agent checking writing rubric scores."""
        from app.agents.critic import CriticAgent
        from app.schemas.agents.all_agents import CriticAgentInput
        
        start_t = datetime.utcnow()
        agent = CriticAgent()
        await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_STARTED, session_id=session_id, data={"agent": agent.name}))
        
        agent_input = CriticAgentInput(
            session_id=session_id,
            draft=draft,
            verified_claims=claims,
            sources=sources,
            revision_number=revision,
            max_revisions=max_rev
        )
        
        try:
            output = await agent.run(agent_input)
            duration = int((datetime.utcnow() - start_t).total_seconds() * 1000)
            
            audit_log = AgentExecutionLog(
                session_id=session_id,
                agent_name=agent.name,
                state_entered=SessionState.CRITIQUE.value,
                duration_ms=duration,
                metadata_json={"score": output.overall_score, "approved": output.approved}
            )
            self.db_session.add(audit_log)
            
            await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_COMPLETED, session_id=session_id, data={"agent": agent.name, "duration_ms": duration}))
            return output
        except Exception as e:
            duration = int((datetime.utcnow() - start_t).total_seconds() * 1000)
            audit_log = AgentExecutionLog(
                session_id=session_id,
                agent_name=agent.name,
                state_entered=SessionState.CRITIQUE.value,
                duration_ms=duration,
                error_message=str(e)
            )
            self.db_session.add(audit_log)
            await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_FAILED, session_id=session_id, data={"agent": agent.name, "error": str(e)}))
            raise AgentExecutionError(message=f"Critic agent failed: {str(e)}") from e

    async def _run_visualization_agent(self, session_id: UUID, report, claims: list, sources: list) -> Any:
        """Produce graph and timeline datasets."""
        from app.agents.visualization import VisualizationAgent
        from app.schemas.agents.all_agents import VisualizationAgentInput
        
        start_t = datetime.utcnow()
        agent = VisualizationAgent()
        await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_STARTED, session_id=session_id, data={"agent": agent.name}))
        
        agent_input = VisualizationAgentInput(
            session_id=session_id,
            report=report,
            verified_claims=claims,
            sources=sources
        )
        
        try:
            output = await agent.run(agent_input)
            duration = int((datetime.utcnow() - start_t).total_seconds() * 1000)
            
            audit_log = AgentExecutionLog(
                session_id=session_id,
                agent_name=agent.name,
                state_entered=SessionState.VISUALIZATION.value,
                duration_ms=duration,
                metadata_json={"nodes_count": len(output.knowledge_nodes), "edges_count": len(output.knowledge_edges)}
            )
            self.db_session.add(audit_log)
            
            await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_COMPLETED, session_id=session_id, data={"agent": agent.name, "duration_ms": duration}))
            return output
        except Exception as e:
            duration = int((datetime.utcnow() - start_t).total_seconds() * 1000)
            audit_log = AgentExecutionLog(
                session_id=session_id,
                agent_name=agent.name,
                state_entered=SessionState.VISUALIZATION.value,
                duration_ms=duration,
                error_message=str(e)
            )
            self.db_session.add(audit_log)
            await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_FAILED, session_id=session_id, data={"agent": agent.name, "error": str(e)}))
            raise AgentExecutionError(message=f"Visualization agent failed: {str(e)}") from e

    async def _run_export_agent(self, session_id: UUID, report, visualization, sources: list) -> Any:
        """Generate PDF file on filesystem."""
        from app.agents.export import ExportAgent
        from app.schemas.agents.all_agents import ExportAgentInput
        
        start_t = datetime.utcnow()
        agent = ExportAgent()
        await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_STARTED, session_id=session_id, data={"agent": agent.name}))
        
        agent_input = ExportAgentInput(
            session_id=session_id,
            report=report,
            visualization=visualization,
            sources=sources
        )
        
        try:
            output = await agent.run(agent_input)
            duration = int((datetime.utcnow() - start_t).total_seconds() * 1000)
            
            audit_log = AgentExecutionLog(
                session_id=session_id,
                agent_name=agent.name,
                state_entered=SessionState.EXPORT.value,
                duration_ms=duration,
                metadata_json={"pdf_file_path": output.pdf_path}
            )
            self.db_session.add(audit_log)
            
            await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_COMPLETED, session_id=session_id, data={"agent": agent.name, "duration_ms": duration}))
            return output
        except Exception as e:
            duration = int((datetime.utcnow() - start_t).total_seconds() * 1000)
            audit_log = AgentExecutionLog(
                session_id=session_id,
                agent_name=agent.name,
                state_entered=SessionState.EXPORT.value,
                duration_ms=duration,
                error_message=str(e)
            )
            self.db_session.add(audit_log)
            await event_broker.publish(session_id, SSEEvent(event=SSEEventType.AGENT_FAILED, session_id=session_id, data={"agent": agent.name, "error": str(e)}))
            raise AgentExecutionError(message=f"Export agent failed: {str(e)}") from e
