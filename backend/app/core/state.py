"""
DSRA V2 — Orchestrator State Machine
======================================
Enforces allowed transitions between ResearchSession states.
Prevents illegal status progression.
"""

from typing import Set

from app.exceptions.base import SessionInvalidStateError
from app.schemas.common import SessionState


class StateMachine:
    """
    State machine helper that validates transition directions.
    """

    # Maps each state to the set of states it is allowed to transition TO.
    _ALLOWED_TRANSITIONS: dict[SessionState, Set[SessionState]] = {
        SessionState.CREATED: {
            SessionState.PLANNING,
            SessionState.FAILED,
            SessionState.CANCELLED,
        },
        SessionState.PLANNING: {
            SessionState.RETRIEVAL,
            SessionState.FAILED,
            SessionState.CANCELLED,
        },
        SessionState.RETRIEVAL: {
            SessionState.EVIDENCE_EXTRACTION,
            SessionState.FAILED,
            SessionState.CANCELLED,
        },
        SessionState.EVIDENCE_EXTRACTION: {
            SessionState.VERIFICATION,
            SessionState.FAILED,
            SessionState.CANCELLED,
        },
        SessionState.VERIFICATION: {
            SessionState.GAP_ANALYSIS,
            SessionState.FAILED,
            SessionState.CANCELLED,
        },
        SessionState.GAP_ANALYSIS: {
            SessionState.ITERATING,
            SessionState.WRITING,
            SessionState.FAILED,
            SessionState.CANCELLED,
        },
        SessionState.ITERATING: {
            SessionState.RETRIEVAL,
            SessionState.FAILED,
            SessionState.CANCELLED,
        },
        SessionState.WRITING: {
            SessionState.CRITIQUE,
            SessionState.FAILED,
            SessionState.CANCELLED,
        },
        SessionState.CRITIQUE: {
            SessionState.WRITING,  # If critique fails and revision is required
            SessionState.VISUALIZATION,  # If approved
            SessionState.FAILED,
            SessionState.CANCELLED,
        },
        SessionState.VISUALIZATION: {
            SessionState.EXPORT,
            SessionState.FAILED,
            SessionState.CANCELLED,
        },
        SessionState.EXPORT: {
            SessionState.COMPLETED,
            SessionState.FAILED,
            SessionState.CANCELLED,
        },
        # Terminal states cannot transition to anything
        SessionState.COMPLETED: set(),
        SessionState.FAILED: set(),
        SessionState.CANCELLED: set(),
    }

    @classmethod
    def validate_transition(cls, current_state: SessionState, target_state: SessionState) -> None:
        """
        Validate whether transitioning from current_state to target_state is legal.
        Raises SessionInvalidStateError if the transition is prohibited.
        """
        # Convert state enums if passed as strings
        curr = SessionState(current_state)
        tgt = SessionState(target_state)

        # Allow transitioning to the same state (idempotency)
        if curr == tgt:
            return

        allowed = cls._ALLOWED_TRANSITIONS.get(curr, set())
        if tgt not in allowed:
            raise SessionInvalidStateError(
                message=f"Illegal transition from state '{curr}' to target state '{tgt}'."
            )
