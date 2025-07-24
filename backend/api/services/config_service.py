"""
Configuration service implementation for the Virtual Coffee Platform.
"""
import logging
from typing import Optional

from backend.api.models.config import (
    ConfigCreate,
    ConfigUpdate,
    DeploymentConfig,
    EmailTemplates,
)
from backend.api.repositories.config_repository import ConfigRepository

logger = logging.getLogger(__name__)


class ConfigService:
    """
    Configuration service implementation for the Virtual Coffee Platform.
    """

    def __init__(self):
        """
        Initialize the configuration service.
        """
        self.repository = ConfigRepository()

    async def create_config(
        self, deployment_id: str, config_create: ConfigCreate
    ) -> DeploymentConfig:
        """
        Create a new deployment configuration.

        Args:
            deployment_id: The ID of the deployment
            config_create: The configuration creation data

        Returns:
            The created configuration
        """
        # Check if config already exists
        existing_config = await self.repository.get(deployment_id)
        if existing_config:
            # Return existing config if found
            return existing_config

        # Create new config
        config = DeploymentConfig(
            deployment_id=deployment_id,
            schedule=config_create.schedule,
            timezone=config_create.timezone or "UTC",
            meeting_size=config_create.meeting_size or 2,
            admin_emails=config_create.admin_emails or [],
            email_templates=config_create.email_templates or EmailTemplates(),
        )

        return await self.repository.create(config)

    async def get_config(self, deployment_id: str) -> Optional[DeploymentConfig]:
        """
        Get a deployment configuration by ID.

        Args:
            deployment_id: The ID of the deployment

        Returns:
            The configuration if found, None otherwise
        """
        return await self.repository.get(deployment_id)

    async def get_all_configs(self) -> list[DeploymentConfig]:
        """
        Get all deployment configurations.

        Returns:
            A list of configurations
        """
        return await self.repository.get_all()

    async def update_config(
        self, deployment_id: str, config_update: ConfigUpdate
    ) -> Optional[DeploymentConfig]:
        """
        Update a deployment configuration.

        Args:
            deployment_id: The ID of the deployment
            config_update: The configuration update data

        Returns:
            The updated configuration if found, None otherwise
        """
        # Convert Pydantic model to dict
        update_dict = config_update.dict(exclude_unset=True)

        return await self.repository.update(deployment_id, update_dict)

    async def update_schedule(
        self, deployment_id: str, schedule: str, timezone: Optional[str] = None
    ) -> Optional[DeploymentConfig]:
        """
        Update a deployment's schedule.

        Args:
            deployment_id: The ID of the deployment
            schedule: The new schedule cron expression
            timezone: The new timezone (optional)

        Returns:
            The updated configuration if found, None otherwise
        """
        update_dict = {"schedule": schedule}

        if timezone:
            update_dict["timezone"] = timezone

        return await self.repository.update(deployment_id, update_dict)

    async def update_meeting_size(
        self, deployment_id: str, meeting_size: int
    ) -> Optional[DeploymentConfig]:
        """
        Update a deployment's meeting size.

        Args:
            deployment_id: The ID of the deployment
            meeting_size: The new meeting size

        Returns:
            The updated configuration if found, None otherwise
        """
        update_dict = {"meeting_size": meeting_size}

        return await self.repository.update(deployment_id, update_dict)

    async def delete_config(self, deployment_id: str) -> bool:
        """
        Delete a deployment configuration.

        Args:
            deployment_id: The ID of the deployment

        Returns:
            True if the configuration was deleted, False otherwise
        """
        return await self.repository.delete(deployment_id)
