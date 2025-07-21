"""
User service implementation for the Virtual Coffee Platform.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.api.models.user import User, UserCreate, UserUpdate
from backend.api.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class UserService:
    """
    User service implementation for the Virtual Coffee Platform.
    """
    
    def __init__(self, deployment_id: str):
        """
        Initialize the user service.
        
        Args:
            deployment_id: The deployment ID for multi-tenancy
        """
        self.deployment_id = deployment_id
        self.repository = UserRepository(deployment_id)
    
    async def register_user(self, user_create: UserCreate) -> User:
        """
        Register a new user.
        
        Args:
            user_create: The user creation data
            
        Returns:
            The created user
        """
        # Check if user already exists
        existing_user = await self.repository.get_by_email(user_create.email)
        if existing_user:
            # Return existing user if found
            return existing_user
        
        # Create new user
        user = User(
            email=user_create.email,
            name=user_create.name,
            deployment_id=self.deployment_id,
            preferences=user_create.preferences or None
        )
        
        return await self.repository.create(user)
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID.
        
        Args:
            user_id: The ID of the user to get
            
        Returns:
            The user if found, None otherwise
        """
        return await self.repository.get(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            email: The email of the user to get
            
        Returns:
            The user if found, None otherwise
        """
        return await self.repository.get_by_email(email)
    
    async def get_all_users(self, active_only: bool = None, paused_only: bool = None) -> List[User]:
        """
        Get all users, optionally filtered.
        
        Args:
            active_only: If True, only return active users
            paused_only: If True, only return paused users
            
        Returns:
            A list of users
        """
        filter_params = {}
        
        if active_only is not None:
            filter_params['is_active'] = active_only
        
        if paused_only is not None:
            filter_params['is_paused'] = paused_only
        
        return await self.repository.get_all(filter_params)
    
    async def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """
        Update a user.
        
        Args:
            user_id: The ID of the user to update
            user_update: The user update data
            
        Returns:
            The updated user if found, None otherwise
        """
        # Convert Pydantic model to dict
        update_dict = user_update.dict(exclude_unset=True)
        
        return await self.repository.update(user_id, update_dict)
    
    async def update_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Optional[User]:
        """
        Update a user's preferences.
        
        Args:
            user_id: The ID of the user to update
            preferences: The preferences to update
            
        Returns:
            The updated user if found, None otherwise
        """
        update_dict = {'preferences': preferences}
        
        return await self.repository.update(user_id, update_dict)
    
    async def toggle_participation(self, user_id: str, is_paused: bool) -> Optional[User]:
        """
        Toggle a user's participation status.
        
        Args:
            user_id: The ID of the user to update
            is_paused: Whether the user is paused
            
        Returns:
            The updated user if found, None otherwise
        """
        update_dict = {'is_paused': is_paused}
        
        return await self.repository.update(user_id, update_dict)
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: The ID of the user to delete
            
        Returns:
            True if the user was deleted, False otherwise
        """
        return await self.repository.delete(user_id)