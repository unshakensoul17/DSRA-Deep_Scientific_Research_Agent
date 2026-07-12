from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from app.schemas.common import VerificationStatus

class ClaimResponse(BaseModel):
    id: UUID
    text: str
    confidence: float
    status: VerificationStatus
    source_ids: List[UUID] = Field(default_factory=list)

    class Config:
        from_attributes = True
