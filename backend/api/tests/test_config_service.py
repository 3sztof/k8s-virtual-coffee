"""
Unit tests for the Configuration service.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from backend.api.models.config import DeploymentConfig, ConfigCreate, ConfigUpdate, EmailTemplates
from backend.api.services.config_service import ConfigService


@pytest.fixture
def mock_config_repository():
    """Create a mock configuration repository."""
    repository = AsyncMock()
    return repository


@pytest.fixture
def config_service(mock_config_repository):
    """Create a configuration service with a mock repository."""
    with patch('backend.api.services.config_service.ConfigRepository', return_value=mock_config_repository):
        service = ConfigService()
        yield service


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    return DeploymentConfig(
        deployment_id="test-deployment",
        schedule="0 9 * * 1",  # Every Monday at 9:00
        timezone="America/New_York",
        meeting_size=2,
        admin_emails=["admin@example.com"],
        email_templates=EmailTemplates(
            match_notification="You have been matched with {{partner_name}}",
            welcome="Welcome to the Virtual Coffee Platform!"
        ),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.mark.asyncio
async def test_create_config_new(config_service, mock_config_repository, sample_config):
    """Test creating a new configuration."""
    # Setup
    mock_config_repository.get.return_value = None
    mock_config_repository.create.return_value = sample_config
    
    config_create = ConfigCreate(
        schedule="0 9 * * 1",
        timezone="America/New_York",
        meeting_size=2,
        admin_emails=["admin@example.com"],
        email_templates=EmailTemplates(
            match_notification="You have been matched with {{partner_name}}",
            welcome="Welcome to the Virtual Coffee Platform!"
        )
    )
    
    # Execute
    result = await config_service.create_config("test-deployment", config_create)
    
    # Assert
    assert result == sample_config
    mock_config_repository.get.assert_called_once_with("test-deployment")
    mock_config_repository.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_config_existing(config_service, mock_config_repository, sample_config):
    """Test creating a configuration that already exists."""
    # Setup
    mock_config_repository.get.return_value = sample_config
    
    config_create = ConfigCreate(
        schedule="0 9 * * 1",
        timezone="America/New_York",
        meeting_size=2
    )
    
    # Execute
    result = await config_service.create_config("test-deployment", config_create)
    
    # Assert
    assert result == sample_config
    mock_config_repository.get.assert_called_once_with("test-deployment")
    mock_config_repository.create.assert_not_called()


@pytest.mark.asyncio
async def test_get_config(config_service, mock_config_repository, sample_config):
    """Test getting a configuration by deployment ID."""
    # Setup
    mock_config_repository.get.return_value = sample_config
    
    # Execute
    result = await config_service.get_config("test-deployment")
    
    # Assert
    assert result == sample_config
    mock_config_repository.get.assert_called_once_with("test-deployment")


@pytest.mark.asyncio
async def test_get_all_configs(config_service, mock_config_repository, sample_config):
    """Test getting all configurations."""
    # Setup
    mock_config_repository.get_all.return_value = [sample_config]
    
    # Execute
    result = await config_service.get_all_configs()
    
    # Assert
    assert result == [sample_config]
    mock_config_repository.get_all.assert_called_once()


@pytest.mark.asyncio
async def test_update_config(config_service, mock_config_repository, sample_config):
    """Test updating a configuration."""
    # Setup
    updated_config = sample_config.copy()
    updated_config.meeting_size = 4
    mock_config_repository.update.return_value = updated_config
    
    config_update = ConfigUpdate(meeting_size=4)
    
    # Execute
    result = await config_service.update_config("test-deployment", config_update)
    
    # Assert
    assert result == updated_config
    mock_config_repository.update.assert_called_once_with("test-deployment", {"meeting_size": 4})


@pytest.mark.asyncio
async def test_update_schedule(config_service, mock_config_repository, sample_config):
    """Test updating a configuration's schedule."""
    # Setup
    updated_config = sample_config.copy()
    updated_config.schedule = "0 10 * * 2"  # Every Tuesday at 10:00
    updated_config.timezone = "UTC"
    mock_config_repository.update.return_value = updated_config
    
    # Execute
    result = await config_service.update_schedule("test-deployment", "0 10 * * 2", "UTC")
    
    # Assert
    assert result == updated_config
    mock_config_repository.update.assert_called_once_with("test-deployment", {
        "schedule": "0 10 * * 2",
        "timezone": "UTC"
    })


@pytest.mark.asyncio
async def test_update_meeting_size(config_service, mock_config_repository, sample_config):
    """Test updating a configuration's meeting size."""
    # Setup
    updated_config = sample_config.copy()
    updated_config.meeting_size = 4
    mock_config_repository.update.return_value = updated_config
    
    # Execute
    result = await config_service.update_meeting_size("test-deployment", 4)
    
    # Assert
    assert result == updated_config
    mock_config_repository.update.assert_called_once_with("test-deployment", {"meeting_size": 4})


@pytest.mark.asyncio
async def test_delete_config(config_service, mock_config_repository):
    """Test deleting a configuration."""
    # Setup
    mock_config_repository.delete.return_value = True
    
    # Execute
    result = await config_service.delete_config("test-deployment")
    
    # Assert
    assert result is True
    mock_config_repository.delete.assert_called_once_with("test-deployment")