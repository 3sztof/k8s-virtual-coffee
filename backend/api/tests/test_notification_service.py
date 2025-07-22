"""
Tests for the notification service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError

from backend.api.models.user import User, Preferences, NotificationPreferences
from backend.api.models.match import Match
from backend.api.services.notification_service import NotificationService


@pytest.fixture
def mock_user_repository():
    """Create a mock user repository."""
    mock = AsyncMock()
    return mock


@pytest.fixture
def mock_match_repository():
    """Create a mock match repository."""
    mock = AsyncMock()
    return mock


@pytest.fixture
def mock_ses_client():
    """Create a mock SES client."""
    mock = MagicMock()
    return mock


@pytest.fixture
def notification_service(mock_user_repository, mock_match_repository, mock_ses_client):
    """Create a notification service with mocked dependencies."""
    with patch('boto3.client', return_value=mock_ses_client):
        service = NotificationService("test-deployment")
        service.user_repository = mock_user_repository
        service.match_repository = mock_match_repository
        service.ses_client = mock_ses_client
        return service


def create_test_user(user_id, name, email=None):
    """Helper function to create test users."""
    return User(
        id=f"user-{user_id}",
        email=email or f"user{user_id}@example.com",
        name=name,
        deployment_id="test-deployment",
        preferences=Preferences(
            topics=["Coffee", "Technology"],
            availability=["Monday 9-10", "Wednesday 14-15"],
            meeting_length=30
        ),
        notification_prefs=NotificationPreferences(
            email=True,
            slack=False,
            telegram=False,
            signal=False,
            primary_channel="email"
        )
    )


def create_test_match(match_id, participants):
    """Helper function to create test matches."""
    return Match(
        id=f"match-{match_id}",
        deployment_id="test-deployment",
        participants=participants,
        scheduled_date=datetime.utcnow() + timedelta(days=1),
        created_at=datetime.utcnow(),
        notification_sent=False
    )


class TestNotificationService:
    """Tests for the NotificationService class."""

    @pytest.mark.asyncio
    async def test_send_match_notification_success(self, notification_service, mock_user_repository, mock_match_repository, mock_ses_client):
        """Test sending match notifications successfully."""
        # Setup
        user1 = create_test_user(1, "User 1")
        user2 = create_test_user(2, "User 2")
        match = create_test_match(1, [user1.id, user2.id])
        
        # Mock repository responses
        mock_user_repository.get.side_effect = lambda user_id: {
            "user-1": user1,
            "user-2": user2
        }.get(user_id)
        
        # Mock SES response
        mock_ses_client.send_email.return_value = {"MessageId": "test-message-id"}
        
        # Execute
        result = await notification_service.send_match_notification(match)
        
        # Verify
        assert result is True
        assert mock_ses_client.send_email.call_count == 2  # One email for each user
        
        # Verify match was updated
        mock_match_repository.update.assert_called_once()
        assert match.notification_sent is True

    @pytest.mark.asyncio
    async def test_send_match_notification_user_not_found(self, notification_service, mock_user_repository, mock_match_repository):
        """Test sending match notifications when a user is not found."""
        # Setup
        user1 = create_test_user(1, "User 1")
        match = create_test_match(1, [user1.id, "user-nonexistent"])
        
        # Mock repository responses
        mock_user_repository.get.side_effect = lambda user_id: {
            "user-1": user1,
            "user-nonexistent": None
        }.get(user_id)
        
        # Execute
        result = await notification_service.send_match_notification(match)
        
        # Verify
        assert result is True  # Should still succeed for the existing user
        mock_match_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_match_notification_ses_error(self, notification_service, mock_user_repository, mock_ses_client):
        """Test sending match notifications with SES error."""
        # Setup
        user1 = create_test_user(1, "User 1")
        user2 = create_test_user(2, "User 2")
        match = create_test_match(1, [user1.id, user2.id])
        
        # Mock repository responses
        mock_user_repository.get.side_effect = lambda user_id: {
            "user-1": user1,
            "user-2": user2
        }.get(user_id)
        
        # Mock SES error
        error_response = {
            "Error": {
                "Code": "MessageRejected",
                "Message": "Email address is not verified"
            }
        }
        mock_ses_client.send_email.side_effect = ClientError(error_response, "SendEmail")
        
        # Execute
        result = await notification_service.send_match_notification(match)
        
        # Verify
        assert result is False  # Should fail due to SES error
        assert notification_service.match_repository.update.call_count == 0  # Match should not be updated

    @pytest.mark.asyncio
    async def test_send_match_notification_retry(self, notification_service, mock_user_repository, mock_ses_client):
        """Test retry logic for sending match notifications."""
        # Setup
        user1 = create_test_user(1, "User 1")
        user2 = create_test_user(2, "User 2")
        match = create_test_match(1, [user1.id, user2.id])
        
        # Mock repository responses
        mock_user_repository.get.side_effect = lambda user_id: {
            "user-1": user1,
            "user-2": user2
        }.get(user_id)
        
        # Mock SES to fail on first attempt for one user, then succeed
        call_count = 0
        
        def mock_send_email(**kwargs):
            nonlocal call_count
            if call_count == 0 and kwargs["Destination"]["ToAddresses"][0] == user1.email:
                call_count += 1
                error_response = {
                    "Error": {
                        "Code": "Throttling",
                        "Message": "Daily message quota exceeded"
                    }
                }
                raise ClientError(error_response, "SendEmail")
            return {"MessageId": "test-message-id"}
        
        mock_ses_client.send_email.side_effect = mock_send_email
        
        # Execute
        with patch.object(notification_service, 'send_match_notification', wraps=notification_service.send_match_notification) as wrapped_method:
            result = await notification_service.send_match_notification(match)
            
            # Verify
            assert result is True  # Should eventually succeed
            assert wrapped_method.call_count > 1  # Should have retried

    @pytest.mark.asyncio
    async def test_send_email_notification(self, notification_service, mock_ses_client):
        """Test sending an email notification."""
        # Setup
        user = create_test_user(1, "User 1")
        other_user = create_test_user(2, "User 2")
        match = create_test_match(1, [user.id, other_user.id])
        
        # Mock SES response
        mock_ses_client.send_email.return_value = {"MessageId": "test-message-id"}
        
        # Execute
        result = await notification_service._send_email_notification(user, match, [other_user])
        
        # Verify
        assert result is True
        mock_ses_client.send_email.assert_called_once()
        
        # Check email content
        call_args = mock_ses_client.send_email.call_args[1]
        assert call_args["Destination"]["ToAddresses"][0] == user.email
        assert "Virtual Coffee Match" in call_args["Message"]["Subject"]["Data"]
        assert user.name in call_args["Message"]["Body"]["Html"]["Data"]
        assert other_user.name in call_args["Message"]["Body"]["Html"]["Data"]
        assert other_user.email in call_args["Message"]["Body"]["Html"]["Data"]