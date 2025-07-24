"""
Integration tests for the User API endpoints.
"""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.models.user import Preferences, User


@pytest.fixture()
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture()
def mock_user_service():
    """Create a mock user service."""
    service = AsyncMock()
    return service


@pytest.fixture()
def sample_user():
    """Create a sample user for testing."""
    return User(
        id="test-user-id",
        email="test@example.com",
        name="Test User",
        deployment_id="test-deployment",
        preferences=Preferences(
            availability=["Monday 9-10", "Wednesday 14-15"],
            topics=["Technology", "Coffee"],
            meeting_length=30,
        ),
        is_active=True,
        is_paused=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture()
def mock_token_data():
    """Create a mock token data object."""
    token_data = MagicMock()
    token_data.sub = "test-user-id"
    token_data.email = "test@example.com"
    token_data.deployment_id = "test-deployment"
    token_data.token_type = "access"
    return token_data


@pytest.fixture()
def mock_get_current_token_data(mock_token_data):
    """Mock the get_current_token_data dependency."""
    with patch("backend.api.main.get_current_token_data", return_value=mock_token_data):
        yield


def test_register_user(
    client, mock_user_service, sample_user, mock_get_current_token_data
):
    """Test the register user endpoint."""
    # Setup
    mock_user_service.register_user.return_value = sample_user

    with patch("backend.api.main.UserService", return_value=mock_user_service):
        # Execute
        response = client.post(
            "/users/register",
            json={
                "email": "test@example.com",
                "name": "Test User",
                "preferences": {
                    "availability": ["Monday 9-10", "Wednesday 14-15"],
                    "topics": ["Technology", "Coffee"],
                    "meeting_length": 30,
                },
            },
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == "test-user-id"
        assert response.json()["email"] == "test@example.com"
        assert response.json()["name"] == "Test User"
        mock_user_service.register_user.assert_called_once()


def test_get_current_user(
    client, mock_user_service, sample_user, mock_get_current_token_data
):
    """Test the get current user endpoint."""
    # Setup
    mock_user_service.get_user.return_value = sample_user

    with patch("backend.api.main.UserService", return_value=mock_user_service):
        # Execute
        response = client.get("/users/me")

        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == "test-user-id"
        assert response.json()["email"] == "test@example.com"
        mock_user_service.get_user.assert_called_once_with("test-user-id")


def test_get_current_user_not_found(
    client, mock_user_service, mock_get_current_token_data
):
    """Test the get current user endpoint when user is not found."""
    # Setup
    mock_user_service.get_user.return_value = None

    with patch("backend.api.main.UserService", return_value=mock_user_service):
        # Execute
        response = client.get("/users/me")

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"
        mock_user_service.get_user.assert_called_once_with("test-user-id")


def test_update_user_profile(
    client, mock_user_service, sample_user, mock_get_current_token_data
):
    """Test the update user profile endpoint."""
    # Setup
    updated_user = sample_user.copy()
    updated_user.name = "Updated Name"
    mock_user_service.update_user.return_value = updated_user

    with patch("backend.api.main.UserService", return_value=mock_user_service):
        # Execute
        response = client.put(
            "/users/profile",
            json={
                "name": "Updated Name",
            },
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"
        mock_user_service.update_user.assert_called_once()


def test_update_user_preferences(
    client, mock_user_service, sample_user, mock_get_current_token_data
):
    """Test the update user preferences endpoint."""
    # Setup
    updated_user = sample_user.copy()
    updated_user.preferences.meeting_length = 45
    mock_user_service.update_preferences.return_value = updated_user

    with patch("backend.api.main.UserService", return_value=mock_user_service):
        # Execute
        response = client.put(
            "/users/preferences",
            json={
                "availability": ["Monday 9-10", "Wednesday 14-15"],
                "topics": ["Technology", "Coffee"],
                "meeting_length": 45,
            },
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["preferences"]["meeting_length"] == 45
        mock_user_service.update_preferences.assert_called_once()


def test_toggle_participation(
    client, mock_user_service, sample_user, mock_get_current_token_data
):
    """Test the toggle participation endpoint."""
    # Setup
    updated_user = sample_user.copy()
    updated_user.is_paused = True
    mock_user_service.toggle_participation.return_value = updated_user

    with patch("backend.api.main.UserService", return_value=mock_user_service):
        # Execute
        response = client.put(
            "/users/participation",
            params={"is_paused": True},
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["is_paused"] is True
        mock_user_service.toggle_participation.assert_called_once_with(
            "test-user-id", True
        )


def test_get_all_users(
    client, mock_user_service, sample_user, mock_get_current_token_data
):
    """Test the get all users endpoint."""
    # Setup
    mock_user_service.get_all_users.return_value = [sample_user]

    with patch("backend.api.main.UserService", return_value=mock_user_service):
        # Execute
        response = client.get("/users")

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == "test-user-id"
        mock_user_service.get_all_users.assert_called_once_with(None, None)


def test_get_all_users_filtered(
    client, mock_user_service, sample_user, mock_get_current_token_data
):
    """Test the get all users endpoint with filters."""
    # Setup
    mock_user_service.get_all_users.return_value = [sample_user]

    with patch("backend.api.main.UserService", return_value=mock_user_service):
        # Execute
        response = client.get("/users?active_only=true&paused_only=false")

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_user_service.get_all_users.assert_called_once_with(True, False)
