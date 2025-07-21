from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict
from datetime import datetime
import re


class EmailTemplates(BaseModel):
    """Email templates for notifications."""
    match_notification: str = Field(
        default="Hello {name}, you've been matched with {partner_names} for a virtual coffee!",
        description="Template for match notification emails"
    )
    reminder: Optional[str] = Field(
        default="Reminder: You have a virtual coffee scheduled with {partner_names} at {time}.",
        description="Template for reminder emails"
    )


class DeploymentConfig(BaseModel):
    """Configuration model for a virtual coffee deployment."""
    deployment_id: str
    schedule: str = Field(
        ...,
        description="Cron expression for the matching schedule"
    )
    timezone: str = Field(
        default="UTC",
        description="Timezone for the deployment"
    )
    meeting_size: int = Field(
        default=2,
        description="Number of participants per meeting",
        ge=2,
        le=10
    )
    admin_emails: List[EmailStr] = Field(
        default_factory=list,
        description="List of admin email addresses"
    )
    email_templates: EmailTemplates = Field(default_factory=EmailTemplates)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('schedule')
    def validate_cron_expression(cls, v):
        # Simple validation for cron expression format
        cron_pattern = r'^(\*|[0-9]{1,2}|\*\/[0-9]{1,2})\s+(\*|[0-9]{1,2}|\*\/[0-9]{1,2})\s+(\*|[0-9]{1,2}|\*\/[0-9]{1,2})\s+(\*|[0-9]{1,2}|\*\/[0-9]{1,2})\s+(\*|[0-6]|\*\/[0-6])$'
        if not re.match(cron_pattern, v):
            raise ValueError('Invalid cron expression format')
        return v

    @validator('timezone')
    def validate_timezone(cls, v):
        # This is a simplified validation - in a real app, we'd check against a list of valid timezones
        if not v:
            raise ValueError('Timezone cannot be empty')
        return v

    class Config:
        schema_extra = {
            "example": {
                "deployment_id": "team-a",
                "schedule": "0 9 * * 1",  # Every Monday at 9 AM
                "timezone": "America/New_York",
                "meeting_size": 2,
                "admin_emails": ["admin@example.com"],
                "email_templates": {
                    "match_notification": "Hello {name}, you've been matched with {partner_names} for a virtual coffee!",
                    "reminder": "Reminder: You have a virtual coffee scheduled with {partner_names} at {time}."
                },
                "created_at": "2023-04-01T12:00:00",
                "updated_at": "2023-04-01T12:00:00"
            }
        }


class ConfigUpdate(BaseModel):
    """Schema for configuration updates."""
    schedule: Optional[str] = None
    timezone: Optional[str] = None
    meeting_size: Optional[int] = None
    admin_emails: Optional[List[EmailStr]] = None
    email_templates: Optional[EmailTemplates] = None

    @validator('schedule')
    def validate_cron_expression(cls, v):
        if v is not None:
            cron_pattern = r'^(\*|[0-9]{1,2}|\*\/[0-9]{1,2})\s+(\*|[0-9]{1,2}|\*\/[0-9]{1,2})\s+(\*|[0-9]{1,2}|\*\/[0-9]{1,2})\s+(\*|[0-9]{1,2}|\*\/[0-9]{1,2})\s+(\*|[0-6]|\*\/[0-6])$'
            if not re.match(cron_pattern, v):
                raise ValueError('Invalid cron expression format')
        return v

    @validator('meeting_size')
    def validate_meeting_size(cls, v):
        if v is not None and (v < 2 or v > 10):
            raise ValueError('Meeting size must be between 2 and 10')
        return v

    class Config:
        schema_extra = {
            "example": {
                "schedule": "0 14 * * 3",  # Every Wednesday at 2 PM
                "timezone": "Europe/London",
                "meeting_size": 3,
                "admin_emails": ["admin@example.com", "manager@example.com"],
                "email_templates": {
                    "match_notification": "Custom match notification template",
                    "reminder": "Custom reminder template"
                }
            }
        }