"""
Unit tests for the User service.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from backend.api.models.user import User, UserCreate, UserUpdate, Preferences
from backend.api.services.user_service import UserService


@pytest.fixture
def mock_user_repository():
    """Create a mock user repository."""
    repository = AsyncMock()
    return repository


@pytest.fixture
def user_service(mock_user_repository):
    """Create a user service with a mock repository."""
    with patch('backend.api.services.user_service.UserRepository', return_value=mock_user_repository):
        service = UserService("test-deployment")
        yield service


@pytest.fixture
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
            meeting_length=30
        ),
        is_active=True,
        is_paused=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.mark.asyncio
async def test_register_user_new(user_service, mock_user_repository, sample_user):
    """Test registering a new user."""
    # Setup
    mock_user_repository.get_by_email.return_value = None
    mock_user_repository.create.return_value = sample_user
    
    user_create = UserCreate(
        email="test@example.com",
        name="Test User",
        preferences=Preferences(
            availability=["Monday 9-10", "Wednesday 14-15"],
            topics=["Technology", "Coffee"],
            meeting_length=30
        )
    )
    
    # Execute
    result = await user_service.register_user(user_create)
    
    # Assert
    assert result == sample_user
    mock_user_repository.get_by_email.assert_called_once_with("test@example.com")
    mock_user_repository.create.assert_called_once()


@pytest.mark.asyncio
async def test_register_user_existing(user_service, mock_user_repository, sample_user):
    """Test registering an existing user."""
    # Setup
    mock_user_repository.get_by_email.return_value = sample_user
    
    user_create = UserCreate(
        email="test@example.com",
        name="Test User",
        preferences=None
    )
    
    # Execute
    result = await user_service.register_user(user_create)
    
    # Assert
    assert result == sample_user
    mock_user_repository.get_by_email.assert_called_once_with("test@example.com")
    mock_user_repository.create.assert_not_called()


@pytest.mark.asyncio
async def test_get_user(user_service, mock_user_repository, sample_user):
    """Test getting a user by ID."""
    # Setup
    mock_user_repository.get.return_value = sample_user
    
    # Execute
    result = await user_service.get_user("test-user-id")
    
    # Assert
    assert result == sample_user
    mock_user_repository.get.assert_called_once_with("test-user-id")


@pytest.mark.asyncio
async def test_get_user_by_email(user_service, mock_user_repository, sample_user):
    """Test getting a user by email."""
    # Setup
    mock_user_repository.get_by_email.return_value = sample_user
    
    # Execute
    result = await user_service.get_user_by_email("test@example.com")
    
    # Assert
    assert result == sample_user
    mock_user_repository.get_by_email.assert_called_once_with("test@example.com")


@pytest.mark.asyncio
async def test_get_all_users(user_service, mock_user_repository, sample_user):
    """Test getting all users."""
    # Setup
    mock_user_repository.get_all.return_value = [sample_user]
    
    # Execute
    result = await user_service.get_all_users()
    
    # Assert
    assert result == [sample_user]
    mock_user_repository.get_all.assert_called_once_with({})


@pytest.mark.asyncio
async def test_get_all_users_filtered(user_service, mock_user_repository, sample_user):
    """Test getting filtered users."""
    # Setup
    mock_user_repository.get_all.return_value = [sample_user]
    
    # Execute
    result = await user_service.get_all_users(active_only=True, paused_only=False)
    
    # Assert
    assert result == [sample_user]
    mock_user_repository.get_all.assert_called_once_with({
        'is_active': True,
        'is_paused': False
    })


@pytest.mark.asyncio
async def test_update_user(user_service, mock_user_repository, sample_user):
    """Test updating a user."""
    # Setup
    updated_user = sample_user.copy()
    updated_user.name = "Updated Name"
    mock_user_repository.update.return_value = updated_user
    
    user_update = UserUpdate(name="Updated Name")
    
    # Execute
    result = await user_service.update_user("test-user-id", user_update)
    
    # Assert
    assert result == updated_user
    mock_user_repository.update.assert_called_once_with("test-user-id", {"name": "Updated Name"})


@pytest.mark.asyncio
async def test_update_preferences(user_service, mock_user_repository, sample_user):
    """Test updating user preferences."""
    # Setup
    updated_user = sample_user.copy()
    updated_user.preferences.meeting_length = 45
    mock_user_repository.update.return_value = updated_user
    
    preferences = {"meeting_length": 45}
    
    # Execute
    result = await user_service.update_preferences("test-user-id", preferences)
    
    # Assert
    assert result == updated_user
    mock_user_repository.update.assert_called_once_with("test-user-id", {"preferences": preferences})


@pytest.mark.asyncio
async def test_toggle_participation(user_service, mock_user_repository, sample_user):
    """Test toggling user participation."""
    # Setup
    updated_user = sample_user.copy()
    updated_user.is_paused = True
    mock_user_repository.update.return_value = updated_user
    
    # Execute
    result = await user_service.toggle_participation("test-user-id", True)
    
    # Assert
    assert result == updated_user
    mock_user_repository.update.assert_called_once_with("test-user-id", {"is_paused": True})


@pytest.mark.asyncio
async def test_delete_user(user_service, mock_user_repository):
    """Test deleting a user."""
    # Setup
    mock_user_repository.delete.return_value = True
    
    # Execute
    result = await user_service.delete_user("test-user-id")
    
    # Assert
    assert result is True
    mock_user_repository.delete.assert_called_once_with("test-user-id")