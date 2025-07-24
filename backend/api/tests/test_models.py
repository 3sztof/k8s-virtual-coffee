from datetime import datetime

import pytest
from pydantic import ValidationError

from models.config import ConfigUpdate, DeploymentConfig, EmailTemplates
from models.match import Match, MatchCreate, MatchUpdate
from models.user import Preferences, User, UserCreate, UserUpdate


class TestUserModels:
    def test_user_creation(self):
        user = User(
            email="test@example.com",
            name="Test User",
            deployment_id="test-team",
        )
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.deployment_id == "test-team"
        assert user.is_active is True
        assert user.is_paused is False
        assert isinstance(user.preferences, Preferences)

    def test_user_with_preferences(self):
        preferences = Preferences(
            availability=["Monday 9-10", "Wednesday 14-15"],
            topics=["Technology", "Coffee"],
            meeting_length=45,
        )
        user = User(
            email="test@example.com",
            name="Test User",
            deployment_id="test-team",
            preferences=preferences,
        )
        assert user.preferences.availability == ["Monday 9-10", "Wednesday 14-15"]
        assert user.preferences.topics == ["Technology", "Coffee"]
        assert user.preferences.meeting_length == 45

    def test_user_name_validation(self):
        with pytest.raises(ValidationError):
            User(
                email="test@example.com",
                name="",  # Empty name should fail validation
                deployment_id="test-team",
            )

    def test_user_create_schema(self):
        user_data = UserCreate(
            email="new@example.com",
            name="New User",
        )
        assert user_data.email == "new@example.com"
        assert user_data.name == "New User"
        assert user_data.preferences is None

    def test_user_update_schema(self):
        update_data = UserUpdate(
            name="Updated Name",
            is_paused=True,
        )
        assert update_data.name == "Updated Name"
        assert update_data.is_paused is True
        assert update_data.preferences is None


class TestMatchModels:
    def test_match_creation(self):
        match = Match(
            deployment_id="test-team",
            participants=["user-1", "user-2"],
            scheduled_date=datetime.utcnow(),
        )
        assert match.deployment_id == "test-team"
        assert match.participants == ["user-1", "user-2"]
        assert match.status == "pending"
        assert match.notification_sent is False

    def test_match_participants_validation(self):
        with pytest.raises(ValidationError):
            Match(
                deployment_id="test-team",
                participants=["user-1"],  # Only one participant should fail
                scheduled_date=datetime.utcnow(),
            )

    def test_match_status_validation(self):
        with pytest.raises(ValidationError):
            Match(
                deployment_id="test-team",
                participants=["user-1", "user-2"],
                scheduled_date=datetime.utcnow(),
                status="invalid-status",  # Invalid status should fail
            )

    def test_match_create_schema(self):
        match_data = MatchCreate(
            participants=["user-1", "user-2"],
            scheduled_date=datetime.utcnow(),
        )
        assert match_data.participants == ["user-1", "user-2"]

    def test_match_update_schema(self):
        update_data = MatchUpdate(
            status="confirmed",
            notification_sent=True,
        )
        assert update_data.status == "confirmed"
        assert update_data.notification_sent is True
        assert update_data.scheduled_date is None


class TestConfigModels:
    def test_config_creation(self):
        config = DeploymentConfig(
            deployment_id="test-team",
            schedule="0 9 * * 1",  # Every Monday at 9 AM
        )
        assert config.deployment_id == "test-team"
        assert config.schedule == "0 9 * * 1"
        assert config.timezone == "UTC"
        assert config.meeting_size == 2
        assert isinstance(config.email_templates, EmailTemplates)

    def test_config_with_custom_values(self):
        templates = EmailTemplates(
            match_notification="Custom match notification",
            reminder="Custom reminder",
        )
        config = DeploymentConfig(
            deployment_id="test-team",
            schedule="0 14 * * 3",  # Every Wednesday at 2 PM
            timezone="Europe/London",
            meeting_size=3,
            admin_emails=["admin@example.com"],
            email_templates=templates,
        )
        assert config.timezone == "Europe/London"
        assert config.meeting_size == 3
        assert config.admin_emails == ["admin@example.com"]
        assert config.email_templates.match_notification == "Custom match notification"

    def test_config_schedule_validation(self):
        with pytest.raises(ValidationError):
            DeploymentConfig(
                deployment_id="test-team",
                schedule="invalid-cron",  # Invalid cron expression should fail
            )

    def test_config_meeting_size_validation(self):
        with pytest.raises(ValidationError):
            DeploymentConfig(
                deployment_id="test-team",
                schedule="0 9 * * 1",
                meeting_size=1,  # Meeting size < 2 should fail
            )

        with pytest.raises(ValidationError):
            DeploymentConfig(
                deployment_id="test-team",
                schedule="0 9 * * 1",
                meeting_size=11,  # Meeting size > 10 should fail
            )

    def test_config_update_schema(self):
        update_data = ConfigUpdate(
            schedule="0 15 * * 5",
            meeting_size=4,
        )
        assert update_data.schedule == "0 15 * * 5"
        assert update_data.meeting_size == 4
        assert update_data.timezone is None
        assert update_data.admin_emails is None
