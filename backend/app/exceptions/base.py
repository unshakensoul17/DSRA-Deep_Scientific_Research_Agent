"""
DSRA V2 — Custom Exception Hierarchy
======================================
Provides a clean, typed exception hierarchy so that:
- Every error has a machine-readable code
- HTTP status codes are centrally defined
- FastAPI exception handlers can pattern-match cleanly
- No generic Exception leaks to the API layer
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DSRABaseError(Exception):
    """
    Root exception for all DSRA V2 application errors.

    Design: Using dataclass to allow structured fields
    without boilerplate __init__ methods.
    """

    message: str
    code: str = "INTERNAL_ERROR"
    http_status: int = 500
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


# ── Authentication & Authorization ────────────────────────────────────────────

@dataclass
class AuthenticationError(DSRABaseError):
    message: str = "Authentication required."
    code: str = "UNAUTHORIZED"
    http_status: int = 401


@dataclass
class InvalidCredentialsError(DSRABaseError):
    message: str = "Invalid email or password."
    code: str = "INVALID_CREDENTIALS"
    http_status: int = 401


@dataclass
class TokenExpiredError(DSRABaseError):
    message: str = "Token has expired."
    code: str = "TOKEN_EXPIRED"
    http_status: int = 401


@dataclass
class InsufficientPermissionsError(DSRABaseError):
    message: str = "You do not have permission to perform this action."
    code: str = "FORBIDDEN"
    http_status: int = 403


# ── Resource Errors ───────────────────────────────────────────────────────────

@dataclass
class ResourceNotFoundError(DSRABaseError):
    message: str = "The requested resource was not found."
    code: str = "NOT_FOUND"
    http_status: int = 404


@dataclass
class ResearchSessionNotFoundError(ResourceNotFoundError):
    message: str = "Research session not found."
    code: str = "RESEARCH_SESSION_NOT_FOUND"


@dataclass
class ReportNotFoundError(ResourceNotFoundError):
    message: str = "Report not found."
    code: str = "REPORT_NOT_FOUND"


@dataclass
class UserNotFoundError(ResourceNotFoundError):
    message: str = "User not found."
    code: str = "USER_NOT_FOUND"


# ── Conflict Errors ───────────────────────────────────────────────────────────

@dataclass
class ConflictError(DSRABaseError):
    message: str = "Resource conflict."
    code: str = "CONFLICT"
    http_status: int = 409


@dataclass
class EmailAlreadyExistsError(ConflictError):
    message: str = "A user with this email already exists."
    code: str = "EMAIL_ALREADY_EXISTS"


@dataclass
class SessionInvalidStateError(ConflictError):
    message: str = "Cannot perform this action in the current session state."
    code: str = "SESSION_INVALID_STATE"


# ── Validation Errors ─────────────────────────────────────────────────────────

@dataclass
class ValidationError(DSRABaseError):
    message: str = "Input validation failed."
    code: str = "VALIDATION_ERROR"
    http_status: int = 422


# ── Agent & Orchestration Errors ──────────────────────────────────────────────

@dataclass
class AgentExecutionError(DSRABaseError):
    message: str = "Agent execution failed."
    code: str = "AGENT_EXECUTION_ERROR"
    http_status: int = 500


@dataclass
class AgentTimeoutError(AgentExecutionError):
    message: str = "Agent execution timed out."
    code: str = "AGENT_TIMEOUT"


@dataclass
class MaxRetriesExceededError(AgentExecutionError):
    message: str = "Maximum retry attempts exceeded."
    code: str = "MAX_RETRIES_EXCEEDED"


# ── LLM Gateway Errors ────────────────────────────────────────────────────────

@dataclass
class LLMGatewayError(DSRABaseError):
    message: str = "LLM provider error."
    code: str = "LLM_GATEWAY_ERROR"
    http_status: int = 503


@dataclass
class LLMRateLimitError(LLMGatewayError):
    message: str = "LLM provider rate limit exceeded."
    code: str = "LLM_RATE_LIMIT"


@dataclass
class LLMInvalidResponseError(LLMGatewayError):
    message: str = "LLM returned an invalid or unparseable response."
    code: str = "LLM_INVALID_RESPONSE"
    http_status: int = 500


# ── Retriever Errors ──────────────────────────────────────────────────────────

@dataclass
class RetrieverError(DSRABaseError):
    message: str = "Source retrieval failed."
    code: str = "RETRIEVER_ERROR"
    http_status: int = 503


@dataclass
class RetrieverTimeoutError(RetrieverError):
    message: str = "Source retrieval timed out."
    code: str = "RETRIEVER_TIMEOUT"


# ── Database Errors ───────────────────────────────────────────────────────────

@dataclass
class DatabaseError(DSRABaseError):
    message: str = "Database operation failed."
    code: str = "DATABASE_ERROR"
    http_status: int = 500


# ── Rate Limit ────────────────────────────────────────────────────────────────

@dataclass
class RateLimitExceededError(DSRABaseError):
    message: str = "Rate limit exceeded. Please wait before making another request."
    code: str = "RATE_LIMIT_EXCEEDED"
    http_status: int = 429
