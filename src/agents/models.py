"""Pydantic models for agent request/response payloads."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator


class RunTurnRequest(BaseModel):
    """Request payload for a single conversation turn.

    Args:
        session_id: Unique identifier for the session.
        role: Role for the incoming message (e.g., user/system).
        content: Message text content.
        turn_id: Monotonic turn index in the conversation.
        metadata: Optional metadata for downstream logging.
        timestamp: Optional ISO timestamp for the turn.
    """

    session_id: str = Field(..., description="Unique identifier for the session.")
    role: str = Field(..., description="Role for the incoming message.")
    content: str = Field(..., description="Message text content.")
    turn_id: int = Field(..., description="Monotonic turn index in the conversation.")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional metadata for the request."
    )
    timestamp: Optional[datetime] = Field(
        default=None,
        description="Optional timestamp for the incoming turn.",
    )

    @field_validator("session_id", "role", "content")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Value must be a non-empty string.")
        return value.strip()

    @field_validator("turn_id")
    @classmethod
    def _validate_turn_id(cls, value: int) -> int:
        if value < 0:
            raise ValueError("turn_id must be a non-negative integer.")
        return value

    @field_validator("timestamp")
    @classmethod
    def _ensure_timezone(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return value
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class RunTurnResponse(BaseModel):
    """Response payload for a single conversation turn.

    Args:
        session_id: Unique identifier for the session.
        role: Role for the response message (assistant).
        content: Response text content.
        turn_id: Turn index corresponding to the request.
        metadata: Optional metadata produced by the agent.
        timestamp: Timestamp when the response was generated.
    """

    session_id: str = Field(..., description="Unique identifier for the session.")
    role: str = Field(..., description="Role for the response message.")
    content: str = Field(..., description="Response text content.")
    turn_id: int = Field(..., description="Turn index corresponding to the request.")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional metadata for the response."
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the response was generated.",
    )

    @field_validator("session_id", "role", "content")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Value must be a non-empty string.")
        return value.strip()

    @field_validator("turn_id")
    @classmethod
    def _validate_turn_id(cls, value: int) -> int:
        if value < 0:
            raise ValueError("turn_id must be a non-negative integer.")
        return value
