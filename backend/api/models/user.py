import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class Preferences(BaseModel):
    """User preferences for coffee meetings."""

    availability: list[str] = Field(
        default_factory=list,
        description="List of available time slots (e.g., 'Monday 9-10')",
    )
    topics: list[str] = Field(
        default_factory=list,
        description="List of topics the user is interested in discussing",
    )
    meeting_length: int = Field(
        default=30,
        description="Preferred meeting length in minutes",
        ge=15,
        le=60,
    )


class User(BaseModel):
    """User model for the Virtual Coffee Platform."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    deployment_id: str
    preferences: Preferences = Field(default_factory=Preferences)
    is_active: bool = True
    is_paused: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator("name")
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "name": "John Doe",
                "deployment_id": "team-a",
                "preferences": {
                    "availability": ["Monday 9-10", "Wednesday 14-15"],
                    "topics": ["Technology", "Coffee", "Books"],
                    "meeting_length": 30,
                },
                "is_active": True,
                "is_paused": False,
                "created_at": "2023-04-01T12:00:00",
                "updated_at": "2023-04-01T12:00:00",
            },
        }


class UserCreate(BaseModel):
    """Schema for user creation."""

    email: EmailStr
    name: str
    preferences: Optional[Preferences] = None

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "name": "John Doe",
                "preferences": {
                    "availability": ["Monday 9-10", "Wednesday 14-15"],
                    "topics": ["Technology", "Coffee", "Books"],
                    "meeting_length": 30,
                },
            },
        }


class UserUpdate(BaseModel):
    """Schema for user updates."""

    name: Optional[str] = None
    preferences: Optional[Preferences] = None
    is_paused: Optional[bool] = None

    class Config:
        schema_extra = {
            "example": {
                "name": "John Doe",
                "preferences": {
                    "availability": ["Monday 9-10", "Wednesday 14-15"],
                    "topics": ["Technology", "Coffee", "Books"],
                    "meeting_length": 30,
                },
                "is_paused": False,
            },
        }
