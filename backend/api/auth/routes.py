"""
Authentication routes for the Virtual Coffee Platform.

This module provides API endpoints for user authentication, including:
- OAuth authentication with various providers
- Token management (refresh, validation)
- User profile retrieval
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Cookie
from fastapi.responses import RedirectResponse
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr

from backend.api.auth.jwt import (
    Token, TokenData, create_tokens, refresh_access_token,
    get_current_token_data, get_current_user_id
)
from backend.api.auth.oauth import (
    OAuthUserInfo, generate_authorization_url, handle_oauth_callback,
    get_deployment_id_from_state, PROVIDERS
)
from backend.api.repositories.user_repository import UserRepository
from backend.api.models.user import User, UserCreate

# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])


class AuthResponse(BaseModel):
    """Authentication response model."""
    token: Token
    user: Dict[str, Any]


class RefreshRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str


class OAuthProviderInfo(BaseModel):
    """OAuth provider information model."""
    id: str
    name: str


@router.get("/providers")
async def get_oauth_providers():
    """
    Get available OAuth providers.
    
    Returns:
        List of available OAuth providers
    """
    return [
        OAuthProviderInfo(id=provider_id, name=provider.name)
        for provider_id, provider in PROVIDERS.items()
    ]


@router.get("/{provider_id}")
async def oauth_login(provider_id: str, request: Request, deployment_id: str):
    """
    Initiate OAuth login flow.
    
    Args:
        provider_id: OAuth provider ID
        request: FastAPI request object
        deployment_id: Deployment ID for multi-tenant support
        
    Returns:
        Redirect to OAuth provider authorization URL
    """
    # Generate the authorization URL
    base_url = str(request.base_url).rstrip("/")
    auth_url = generate_authorization_url(provider_id, base_url, deployment_id)
    
    # Redirect to the authorization URL
    return RedirectResponse(auth_url)


@router.get("/{provider_id}/callback")
async def oauth_callback(
    provider_id: str,
    code: str,
    state: str,
    request: Request,
    response: Response
):
    """
    Handle OAuth callback from provider.
    
    Args:
        provider_id: OAuth provider ID
        code: Authorization code from the provider
        state: State parameter from the provider
        request: FastAPI request object
        response: FastAPI response object
        
    Returns:
        Authentication response with tokens and user information
    """
    # Get user information from the OAuth provider
    user_info = await handle_oauth_callback(provider_id, code, state)
    
    # Get deployment ID from state
    deployment_id = get_deployment_id_from_state(state)
    
    # Create or update user in the database
    user_repository = UserRepository(deployment_id)
    
    # Check if user exists
    existing_user = await user_repository.find_by_email(user_info.email)
    
    if existing_user:
        # Update existing user with latest OAuth information
        user = existing_user
    else:
        # Create new user
        new_user = UserCreate(
            email=user_info.email,
            name=user_info.name or user_info.email.split("@")[0],
            oauth_provider=user_info.provider,
            oauth_provider_user_id=user_info.provider_user_id
        )
        user = User(
            email=new_user.email,
            name=new_user.name,
            deployment_id=deployment_id,
            oauth_provider=new_user.oauth_provider,
            oauth_provider_user_id=new_user.oauth_provider_user_id,
            is_active=True,
            is_paused=False
        )
        user = await user_repository.create(user)
    
    # Create tokens
    tokens = create_tokens(user.id, user.email, deployment_id)
    
    # Set cookies for frontend
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=900  # 15 minutes
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=604800  # 7 days
    )
    
    # Redirect to frontend with success
    frontend_url = f"https://virtual-coffee.example.com/{deployment_id}"
    return RedirectResponse(f"{frontend_url}/auth/success")


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_request: RefreshRequest):
    """
    Refresh access token using a valid refresh token.
    
    Args:
        refresh_request: Refresh token request
        
    Returns:
        New access token and the same refresh token
    """
    return refresh_access_token(refresh_request.refresh_token)


@router.post("/logout")
async def logout(response: Response):
    """
    Logout the current user by clearing authentication cookies.
    
    Args:
        response: FastAPI response object
        
    Returns:
        Success message
    """
    # Clear authentication cookies
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    
    return {"message": "Successfully logged out"}


@router.get("/me")
async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    token_data: TokenData = Depends(get_current_token_data)
):
    """
    Get the current authenticated user.
    
    Args:
        user_id: Current user ID from token
        token_data: Current token data
        
    Returns:
        Current user information
    """
    # Get user from database
    user_repository = UserRepository(token_data.deployment_id)
    user = await user_repository.get(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user