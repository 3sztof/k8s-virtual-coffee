"""
Tests for the scheduler component.
"""
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from backend.api.models.config import DeploymentConfig
from backend.api.scheduler.scheduler import MatchingScheduler


@pytest.fixture()
def mock_config_service():
    """Create a mock configuration service."""
    mock = AsyncMock()
    return mock


@pytest.fixture()
def scheduler(mock_config_service):
    """Create a scheduler with a mock config service."""
    with patch(
        "backend.api.scheduler.scheduler.ConfigService",
        return_value=mock_config_service,
    ):
        scheduler = MatchingScheduler()
        yield scheduler


@pytest.fixture()
def sample_config():
    """Create a sample configuration for testing."""
    return DeploymentConfig(
        deployment_id="test-deployment",
        schedule="0 9 * * 1",  # Every Monday at 9:00
        timezone="America/New_York",
        meeting_size=2,
    )


@pytest.mark.asyncio()
async def test_get_schedule_info_valid(scheduler, sample_config):
    """Test getting schedule information with a valid configuration."""
    # Execute
    result = await scheduler.get_schedule_info(sample_config)

    # Verify
    assert result["valid"] is True
    assert result["cron"] == "0 9 * * 1"
    assert result["timezone"] == "America/New_York"
    assert result["deployment_id"] == "test-deployment"
    assert result["meeting_size"] == 2
    assert "next_run_utc" in result


@pytest.mark.asyncio()
async def test_get_schedule_info_invalid_cron(scheduler):
    """Test getting schedule information with an invalid cron expression."""
    # Setup
    invalid_config = DeploymentConfig(
        deployment_id="test-deployment",
        schedule="invalid",  # Invalid cron expression
        timezone="America/New_York",
    )

    # Execute
    result = await scheduler.get_schedule_info(invalid_config)

    # Verify
    assert result["valid"] is False
    assert "error" in result


@pytest.mark.asyncio()
async def test_get_schedule_info_invalid_timezone(scheduler):
    """Test getting schedule information with an invalid timezone."""
    # Setup
    invalid_config = DeploymentConfig(
        deployment_id="test-deployment",
        schedule="0 9 * * 1",
        timezone="Invalid/Timezone",  # Invalid timezone
    )

    # Execute
    result = await scheduler.get_schedule_info(invalid_config)

    # Verify
    assert result["valid"] is False
    assert "error" in result
    assert "timezone" in result["error"]


@pytest.mark.asyncio()
async def test_get_all_schedules(scheduler, mock_config_service, sample_config):
    """Test getting all schedules."""
    # Setup
    mock_config_service.get_all_configs.return_value = [sample_config]

    # Mock get_schedule_info to return a valid schedule
    scheduler.get_schedule_info = AsyncMock()
    scheduler.get_schedule_info.return_value = {
        "valid": True,
        "cron": "0 9 * * 1",
        "timezone": "America/New_York",
        "next_run_utc": datetime.utcnow().isoformat(),
        "deployment_id": "test-deployment",
        "meeting_size": 2,
    }

    # Execute
    result = await scheduler.get_all_schedules()

    # Verify
    assert "test-deployment" in result
    assert result["test-deployment"]["valid"] is True
    mock_config_service.get_all_configs.assert_called_once()
    scheduler.get_schedule_info.assert_called_once_with(sample_config)


def test_generate_cronjob_manifest(scheduler):
    """Test generating a Kubernetes CronJob manifest."""
    # Execute
    result = scheduler.generate_cronjob_manifest(
        "test-deployment",
        "0 9 * * 1",
        "America/New_York",
    )

    # Verify
    assert result["kind"] == "CronJob"
    assert result["metadata"]["name"] == "virtual-coffee-matching-test-deployment"
    assert result["spec"]["schedule"] == "0 9 * * 1"
    assert result["spec"]["timeZone"] == "America/New_York"

    # Check that the container has the right command and environment
    container = result["spec"]["jobTemplate"]["spec"]["template"]["spec"]["containers"][
        0
    ]
    assert "run_matching" in container["command"]

    env = {e["name"]: e["value"] for e in container["env"]}
    assert env["DEPLOYMENT_ID"] == "test-deployment"


def test_generate_argocd_workflow(scheduler):
    """Test generating an ArgoCD Workflow manifest."""
    # Execute
    result = scheduler.generate_argocd_workflow(
        "test-deployment",
        "0 9 * * 1",
        "America/New_York",
    )

    # Verify
    assert result["kind"] == "Workflow"
    assert result["metadata"]["name"] == "virtual-coffee-matching-test-deployment"

    # Check that the workflow has the right steps
    templates = {t["name"]: t for t in result["spec"]["templates"]}
    assert "matching-workflow" in templates
    assert "run-matching" in templates
    assert "send-notifications" in templates

    # Check that the deployment ID is passed correctly
    assert result["spec"]["arguments"]["parameters"][0]["value"] == "test-deployment"


@pytest.mark.asyncio()
async def test_apply_schedule(scheduler, mock_config_service, sample_config):
    """Test applying a schedule."""
    # Setup
    mock_config_service.get_config.return_value = sample_config

    # Mock get_schedule_info to return a valid schedule
    scheduler.get_schedule_info = AsyncMock()
    scheduler.get_schedule_info.return_value = {
        "valid": True,
        "cron": "0 9 * * 1",
        "timezone": "America/New_York",
        "next_run_utc": datetime.utcnow().isoformat(),
        "deployment_id": "test-deployment",
        "meeting_size": 2,
    }

    # Execute
    result = await scheduler.apply_schedule("test-deployment")

    # Verify
    assert result is True
    mock_config_service.get_config.assert_called_once_with("test-deployment")
    scheduler.get_schedule_info.assert_called_once_with(sample_config)


@pytest.mark.asyncio()
async def test_apply_schedule_no_config(scheduler, mock_config_service):
    """Test applying a schedule with no configuration."""
    # Setup
    mock_config_service.get_config.return_value = None

    # Execute
    result = await scheduler.apply_schedule("test-deployment")

    # Verify
    assert result is False
    mock_config_service.get_config.assert_called_once_with("test-deployment")


@pytest.mark.asyncio()
async def test_apply_schedule_invalid_schedule(
    scheduler, mock_config_service, sample_config
):
    """Test applying a schedule with an invalid schedule."""
    # Setup
    mock_config_service.get_config.return_value = sample_config

    # Mock get_schedule_info to return an invalid schedule
    scheduler.get_schedule_info = AsyncMock()
    scheduler.get_schedule_info.return_value = {
        "valid": False,
        "error": "Invalid schedule",
    }

    # Execute
    result = await scheduler.apply_schedule("test-deployment")

    # Verify
    assert result is False
    mock_config_service.get_config.assert_called_once_with("test-deployment")
    scheduler.get_schedule_info.assert_called_once_with(sample_config)


@pytest.mark.asyncio()
async def test_remove_schedule(scheduler):
    """Test removing a schedule."""
    # Execute
    result = await scheduler.remove_schedule("test-deployment")

    # Verify
    assert result is True
