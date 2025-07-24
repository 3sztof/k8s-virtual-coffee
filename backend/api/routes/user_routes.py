"""
User management routes for the Virtual Coffee Platform.

This module provides API endpoints for user management, including:
- User registration and profile updates
- Preference management
- Participation status toggling
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.api.auth.jwt import TokenData, get_current_token_data, get_current_user_id
from backend.api.models.user import Preferences, User, UserCreate, UserUpdate
from backend.api.repositories.user_repository import UserRepository

# Create router
router = APIRouter(prefix="/users", tags=["users"])


class ParticipationUpdate(BaseModel):
    """Participation status update model."""

    is_paused: bool


class PreferencesUpdate(BaseModel):
    """User preferences update model."""

    topics: Optional[list[str]] = None
    availability: Optional[list[str]] = None
    meeting_length: Optional[int] = None


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=User)
async def register_user(
    user_create: UserCreate,
    deployment_id: str,
    token_data: TokenData = Depends(get_current_token_data),
):
    """
    Register a new user.

    Args:
        user_create: User creation data
        deployment_id: Deployment ID for multi-tenant support
        token_data: Current token data

    Returns:
        Created user

    Raises:
        HTTPException: If user already exists or validation fails
    """
    # Ensure the deployment ID matches the token
    if deployment_id != token_data.deployment_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Deployment ID mismatch",
        )

    # Create user repository
    user_repository = UserRepository(deployment_id)

    # Check if user already exists
    existing_user = await user_repository.find_by_email(user_create.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    # Create user
    user = User(
        email=user_create.email,
        name=user_create.name,
        deployment_id=deployment_id,
        oauth_provider=user_create.oauth_provider,
        oauth_provider_user_id=user_create.oauth_provider_user_id,
        is_active=True,
        is_paused=False,
    )

    # Save user to database
    created_user = await user_repository.create(user)
    return created_user


@router.get("/profile", response_model=User)
async def get_user_profile(
    user_id: str = Depends(get_current_user_id),
    token_data: TokenData = Depends(get_current_token_data),
):
    """
    Get the current user's profile.

    Args:
        user_id: Current user ID from token
        token_data: Current token data

    Returns:
        User profile

    Raises:
        HTTPException: If user not found
    """
    # Create user repository
    user_repository = UserRepository(token_data.deployment_id)

    # Get user from database
    user = await user_repository.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.put("/profile", response_model=User)
async def update_user_profile(
    user_update: UserUpdate,
    user_id: str = Depends(get_current_user_id),
    token_data: TokenData = Depends(get_current_token_data),
):
    """
    Update the current user's profile.

    Args:
        user_update: User update data
        user_id: Current user ID from token
        token_data: Current token data

    Returns:
        Updated user profile

    Raises:
        HTTPException: If user not found
    """
    # Create user repository
    user_repository = UserRepository(token_data.deployment_id)

    # Get user from database
    user = await user_repository.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update user fields
    if user_update.name is not None:
        user.name = user_update.name

    if user_update.notification_prefs is not None:
        user.notification_prefs = user_update.notification_prefs

    # Save updated user to database
    updated_user = await user_repository.update(user)
    return updated_user


@router.put("/preferences", response_model=User)
async def update_user_preferences(
    preferences: PreferencesUpdate,
    user_id: str = Depends(get_current_user_id),
    token_data: TokenData = Depends(get_current_token_data),
):
    """
    Update the current user's preferences.

    Args:
        preferences: Preferences update data
        user_id: Current user ID from token
        token_data: Current token data

    Returns:
        Updated user profile

    Raises:
        HTTPException: If user not found
    """
    # Create user repository
    user_repository = UserRepository(token_data.deployment_id)

    # Get user from database
    user = await user_repository.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Initialize preferences if not exists
    if not user.preferences:
        user.preferences = Preferences()

    # Update preferences fields
    if preferences.topics is not None:
        user.preferences.topics = preferences.topics

    if preferences.availability is not None:
        user.preferences.availability = preferences.availability

    if preferences.meeting_length is not None:
        user.preferences.meeting_length = preferences.meeting_length

    # Save updated user to database
    updated_user = await user_repository.update(user)
    return updated_user


@router.put("/participation", response_model=User)
async def update_participation_status(
    participation: ParticipationUpdate,
    user_id: str = Depends(get_current_user_id),
    token_data: TokenData = Depends(get_current_token_data),
):
    """
    Update the current user's participation status.

    Args:
        participation: Participation status update
        user_id: Current user ID from token
        token_data: Current token data

    Returns:
        Updated user profile

    Raises:
        HTTPException: If user not found
    """
    # Create user repository
    user_repository = UserRepository(token_data.deployment_id)

    # Get user from database
    user = await user_repository.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update participation status
    user.is_paused = participation.is_paused

    # Save updated user to database
    updated_user = await user_repository.update(user)
    return updated_user


@router.get("/", response_model=list[User])
async def get_all_users(
    token_data: TokenData = Depends(get_current_token_data),
):
    """
    Get all users in the current deployment.

    Args:
        token_data: Current token data

    Returns:
        List of users
    """
    # Create user repository
    user_repository = UserRepository(token_data.deployment_id)

    # Get all users from database
    users = await user_repository.get_all()
    return users
