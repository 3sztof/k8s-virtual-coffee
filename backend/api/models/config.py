"""
Configuration models for the Virtual Coffee Platform.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


class EmailTemplates(BaseModel):
    """Email templates for notifications."""

    match_notification: str = Field(
        default="",
        description="Template for match notifications",
    )
    welcome: str = Field(
        default="",
        description="Template for welcome emails",
    )


class DeploymentConfig(BaseModel):
    """Deployment configuration model for the Virtual Coffee Platform."""

    deployment_id: str
    schedule: str = Field(
        description="Cron expression for the matching schedule",
    )
    timezone: str = Field(
        default="UTC",
        description="Timezone for the schedule",
    )
    meeting_size: int = Field(
        default=2,
        description="Number of participants per meeting",
        ge=2,
        le=10,
    )
    admin_emails: list[str] = Field(
        default_factory=list,
        description="List of admin email addresses",
    )
    email_templates: EmailTemplates = Field(
        default_factory=EmailTemplates,
        description="Email templates for notifications",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator("schedule")
    def validate_schedule(cls, v):
        """Validate the schedule cron expression."""
        # Basic validation for cron expression format
        parts = v.split()
        if len(parts) != 5:
            raise ValueError("Schedule must be a valid cron expression with 5 parts")
        return v

    @validator("timezone")
    def validate_timezone(cls, v):
        """Validate the timezone."""
        # This is a simplified validation
        # In a real application, you would validate against a list of valid timezones
        if not v:
            raise ValueError("Timezone cannot be empty")
        return v

    class Config:
        schema_extra = {
            "example": {
                "deployment_id": "team-a",
                "schedule": "0 9 * * 1",  # Every Monday at 9:00
                "timezone": "America/New_York",
                "meeting_size": 2,
                "admin_emails": ["admin@example.com"],
                "email_templates": {
                    "match_notification": "You have been matched with {{partner_name}}",
                    "welcome": "Welcome to the Virtual Coffee Platform!",
                },
                "created_at": "2023-04-01T12:00:00",
                "updated_at": "2023-04-01T12:00:00",
            },
        }


class ConfigCreate(BaseModel):
    """Schema for configuration creation."""

    schedule: str
    timezone: Optional[str] = "UTC"
    meeting_size: Optional[int] = 2
    admin_emails: Optional[list[str]] = None
    email_templates: Optional[EmailTemplates] = None

    class Config:
        schema_extra = {
            "example": {
                "schedule": "0 9 * * 1",  # Every Monday at 9:00
                "timezone": "America/New_York",
                "meeting_size": 2,
                "admin_emails": ["admin@example.com"],
                "email_templates": {
                    "match_notification": "You have been matched with {{partner_name}}",
                    "welcome": "Welcome to the Virtual Coffee Platform!",
                },
            },
        }


class ConfigUpdate(BaseModel):
    """Schema for configuration updates."""

    schedule: Optional[str] = None
    timezone: Optional[str] = None
    meeting_size: Optional[int] = None
    admin_emails: Optional[list[str]] = None
    email_templates: Optional[EmailTemplates] = None

    class Config:
        schema_extra = {
            "example": {
                "schedule": "0 9 * * 1",  # Every Monday at 9:00
                "timezone": "America/New_York",
                "meeting_size": 2,
                "admin_emails": ["admin@example.com"],
                "email_templates": {
                    "match_notification": "You have been matched with {{partner_name}}",
                    "welcome": "Welcome to the Virtual Coffee Platform!",
                },
            },
        }
