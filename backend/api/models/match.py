import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


class Match(BaseModel):
    """Match model for the Virtual Coffee Platform."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    deployment_id: str
    participants: list[str] = Field(
        ...,
        description="List of user IDs participating in this match",
    )
    scheduled_date: datetime
    status: str = "pending"  # pending, confirmed, completed, cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notification_sent: bool = False

    @validator("participants")
    def validate_participants(cls, v):
        if len(v) < 2:
            raise ValueError("A match must have at least 2 participants")
        return v

    @validator("status")
    def validate_status(cls, v):
        valid_statuses = ["pending", "confirmed", "completed", "cancelled"]
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v

    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "deployment_id": "team-a",
                "participants": [
                    "user-id-1",
                    "user-id-2",
                ],
                "scheduled_date": "2023-04-15T14:00:00",
                "status": "pending",
                "created_at": "2023-04-01T12:00:00",
                "notification_sent": False,
            },
        }


class MatchCreate(BaseModel):
    """Schema for match creation."""

    participants: list[str]
    scheduled_date: datetime

    class Config:
        schema_extra = {
            "example": {
                "participants": [
                    "user-id-1",
                    "user-id-2",
                ],
                "scheduled_date": "2023-04-15T14:00:00",
            },
        }


class MatchUpdate(BaseModel):
    """Schema for match updates."""

    scheduled_date: Optional[datetime] = None
    status: Optional[str] = None
    notification_sent: Optional[bool] = None

    @validator("status")
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ["pending", "confirmed", "completed", "cancelled"]
            if v not in valid_statuses:
                raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v

    class Config:
        schema_extra = {
            "example": {
                "scheduled_date": "2023-04-15T15:00:00",
                "status": "confirmed",
                "notification_sent": True,
            },
        }
