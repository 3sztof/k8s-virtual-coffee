from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
import uvicorn
from typing import List, Optional

from backend.api.auth.jwt import (
    create_tokens, 
    refresh_access_token, 
    get_current_user_id,
    get_current_token_data,
    Token,
    TokenData,
)
from backend.api.auth.middleware import JWTAuthMiddleware
from backend.api.auth.oauth import (
    generate_authorization_url,
    handle_oauth_callback,
    get_deployment_id_from_state,
)
from backend.api.models.user import User, UserCreate, UserUpdate, Preferences
from backend.api.models.config import DeploymentConfig, ConfigCreate, ConfigUpdate, EmailTemplates
from backend.api.services.user_service import UserService
from backend.api.services.config_service import ConfigService

app = FastAPI(
    title="Virtual Coffee Platform API",
    description="API for the Virtual Coffee Platform",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add JWT authentication middleware
app.middleware("http")(JWTAuthMiddleware())

# Authentication routes
@app.post("/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Get an access token for authentication.
    
    This is a placeholder implementation. In a real application, you would:
    1. Verify the user credentials against a database
    2. Create tokens only for valid users
    
    For now, we'll create tokens for any username/password for testing purposes.
    """
    # TODO: Implement actual user authentication against database
    # For now, we'll use the username as both user_id and email for testing
    user_id = form_data.username
    email = f"{form_data.username}@example.com"
    deployment_id = "default-deployment"
    
    # Create access and refresh tokens
    tokens = create_tokens(user_id, email, deployment_id)
    
    return tokens

@app.post("/auth/refresh", response_model=Token)
async def refresh_token(request: Request):
    """
    Get a new access token using a refresh token.
    
    The refresh token should be provided in the Authorization header
    as a Bearer token.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    scheme, token = auth_header.split()
    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new access token using the provided refresh token
    new_tokens = refresh_access_token(token)
    
    return new_tokens

@app.get("/")
async def root():
    return {"message": "Welcome to the Virtual Coffee Platform API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# OAuth authentication routes
@app.get("/auth/{provider}")
async def oauth_login(provider: str, request: Request, response: Response, deployment_id: str = "default-deployment"):
    """
    Initiate OAuth authentication flow with the specified provider.
    
    Args:
        provider: OAuth provider ID (amazon-sso, amazon, or google)
        request: FastAPI request object
        response: FastAPI response object
        deployment_id: Deployment ID for multi-tenant support
    
    Returns:
        Redirect to the OAuth provider's authorization URL
    """
    # Get the base URL from the request
    base_url = str(request.base_url).rstrip("/")
    
    try:
        # Generate the authorization URL
        auth_url = generate_authorization_url(provider, base_url, deployment_id)
        
        # Redirect to the authorization URL
        return RedirectResponse(url=auth_url)
    except HTTPException as e:
        return {"error": e.detail, "status_code": e.status_code}

@app.get("/auth/{provider}/callback")
async def oauth_callback(provider: str, code: str, state: str, request: Request):
    """
    Handle OAuth callback from the provider.
    
    Args:
        provider: OAuth provider ID (amazon-sso, amazon, or google)
        code: Authorization code from the provider
        state: State parameter from the provider
        request: FastAPI request object
    
    Returns:
        JWT tokens for the authenticated user or redirect to frontend with tokens
    """
    try:
        # Handle the OAuth callback
        user_info = await handle_oauth_callback(provider, code, state)
        
        # Get the deployment ID from the state parameter
        deployment_id = get_deployment_id_from_state(state)
        
        # Create JWT tokens for the user
        # Use the provider user ID as the user ID and the email from the user info
        tokens = create_tokens(
            user_id=f"{provider}:{user_info.provider_user_id}",
            email=user_info.email,
            deployment_id=deployment_id
        )
        
        # In a real application, you would:
        # 1. Check if the user exists in your database
        # 2. Create a new user if they don't exist
        # 3. Update the user's information if they do exist
        # 4. Redirect to a frontend page with the tokens
        
        # For demonstration purposes, we'll create a simple HTML response with the tokens
        # In production, you would redirect to your frontend application
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Successful</title>
            <script>
                // Store tokens in localStorage
                localStorage.setItem('access_token', '{tokens.access_token}');
                localStorage.setItem('refresh_token', '{tokens.refresh_token}');
                
                // Redirect to the main application
                window.location.href = '/';
            </script>
        </head>
        <body>
            <h1>Authentication Successful</h1>
            <p>You have successfully authenticated with {user_info.provider}.</p>
            <p>Redirecting to the application...</p>
        </body>
        </html>
        """
        
        return Response(content=html_content, media_type="text/html")
    except HTTPException as e:
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Error</title>
        </head>
        <body>
            <h1>Authentication Error</h1>
            <p>Error: {e.detail}</p>
            <p>Status Code: {e.status_code}</p>
            <a href="/">Return to Home</a>
        </body>
        </html>
        """
        return Response(content=error_html, media_type="text/html", status_code=e.status_code)

# User service endpoints
@app.post("/users/register", response_model=User)
async def register_user(user_create: UserCreate, token_data: TokenData = Depends(get_current_token_data)):
    """
    Register a new user.
    
    This endpoint creates a new user with the provided information.
    If the user already exists (based on email), it returns the existing user.
    
    Args:
        user_create: User creation data
        token_data: JWT token data from the request
        
    Returns:
        The created or existing user
    """
    # Create user service with deployment ID from token
    user_service = UserService(token_data.deployment_id)
    
    # Register the user
    user = await user_service.register_user(user_create)
    
    return user

@app.get("/users/me", response_model=User)
async def get_current_user(token_data: TokenData = Depends(get_current_token_data)):
    """
    Get the current authenticated user.
    
    This is a protected route that requires a valid JWT token.
    
    Args:
        token_data: JWT token data from the request
        
    Returns:
        The current user
        
    Raises:
        HTTPException: If the user is not found
    """
    # Create user service with deployment ID from token
    user_service = UserService(token_data.deployment_id)
    
    # Get the user by ID from the token
    user = await user_service.get_user(token_data.sub)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@app.put("/users/profile", response_model=User)
async def update_user_profile(
    user_update: UserUpdate,
    token_data: TokenData = Depends(get_current_token_data)
):
    """
    Update the current user's profile.
    
    Args:
        user_update: User update data
        token_data: JWT token data from the request
        
    Returns:
        The updated user
        
    Raises:
        HTTPException: If the user is not found
    """
    # Create user service with deployment ID from token
    user_service = UserService(token_data.deployment_id)
    
    # Update the user
    updated_user = await user_service.update_user(token_data.sub, user_update)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return updated_user

@app.put("/users/preferences", response_model=User)
async def update_user_preferences(
    preferences: Preferences,
    token_data: TokenData = Depends(get_current_token_data)
):
    """
    Update the current user's preferences.
    
    Args:
        preferences: User preferences
        token_data: JWT token data from the request
        
    Returns:
        The updated user
        
    Raises:
        HTTPException: If the user is not found
    """
    # Create user service with deployment ID from token
    user_service = UserService(token_data.deployment_id)
    
    # Update the user's preferences
    updated_user = await user_service.update_preferences(token_data.sub, preferences.dict())
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return updated_user

@app.put("/users/participation", response_model=User)
async def toggle_participation(
    is_paused: bool,
    token_data: TokenData = Depends(get_current_token_data)
):
    """
    Toggle the current user's participation status.
    
    Args:
        is_paused: Whether the user is paused
        token_data: JWT token data from the request
        
    Returns:
        The updated user
        
    Raises:
        HTTPException: If the user is not found
    """
    # Create user service with deployment ID from token
    user_service = UserService(token_data.deployment_id)
    
    # Toggle the user's participation status
    updated_user = await user_service.toggle_participation(token_data.sub, is_paused)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return updated_user

@app.get("/users", response_model=List[User])
async def get_all_users(
    active_only: Optional[bool] = None,
    paused_only: Optional[bool] = None,
    token_data: TokenData = Depends(get_current_token_data)
):
    """
    Get all users, optionally filtered.
    
    Args:
        active_only: If True, only return active users
        paused_only: If True, only return paused users
        token_data: JWT token data from the request
        
    Returns:
        A list of users
    """
    # Create user service with deployment ID from token
    user_service = UserService(token_data.deployment_id)
    
    # Get all users with optional filters
    users = await user_service.get_all_users(active_only, paused_only)
    
    return users

# Configuration service endpoints
@app.post("/config", response_model=DeploymentConfig)
async def create_deployment_config(
    config_create: ConfigCreate,
    token_data: TokenData = Depends(get_current_token_data)
):
    """
    Create a new deployment configuration.
    
    Args:
        config_create: Configuration creation data
        token_data: JWT token data from the request
        
    Returns:
        The created configuration
    """
    # Create config service
    config_service = ConfigService()
    
    # Create the configuration
    config = await config_service.create_config(token_data.deployment_id, config_create)
    
    return config

@app.get("/config", response_model=DeploymentConfig)
async def get_deployment_config(token_data: TokenData = Depends(get_current_token_data)):
    """
    Get the current deployment configuration.
    
    Args:
        token_data: JWT token data from the request
        
    Returns:
        The deployment configuration
        
    Raises:
        HTTPException: If the configuration is not found
    """
    # Create config service
    config_service = ConfigService()
    
    # Get the configuration
    config = await config_service.get_config(token_data.deployment_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    
    return config

@app.put("/config", response_model=DeploymentConfig)
async def update_deployment_config(
    config_update: ConfigUpdate,
    token_data: TokenData = Depends(get_current_token_data)
):
    """
    Update the current deployment configuration.
    
    Args:
        config_update: Configuration update data
        token_data: JWT token data from the request
        
    Returns:
        The updated configuration
        
    Raises:
        HTTPException: If the configuration is not found
    """
    # Create config service
    config_service = ConfigService()
    
    # Update the configuration
    updated_config = await config_service.update_config(token_data.deployment_id, config_update)
    
    if not updated_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    
    return updated_config

@app.put("/config/schedule", response_model=DeploymentConfig)
async def update_schedule(
    schedule: str,
    timezone: Optional[str] = None,
    token_data: TokenData = Depends(get_current_token_data)
):
    """
    Update the deployment schedule.
    
    Args:
        schedule: The new schedule cron expression
        timezone: The new timezone (optional)
        token_data: JWT token data from the request
        
    Returns:
        The updated configuration
        
    Raises:
        HTTPException: If the configuration is not found
    """
    # Create config service
    config_service = ConfigService()
    
    # Update the schedule
    updated_config = await config_service.update_schedule(token_data.deployment_id, schedule, timezone)
    
    if not updated_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    
    return updated_config

@app.put("/config/meeting-size", response_model=DeploymentConfig)
async def update_meeting_size(
    meeting_size: int,
    token_data: TokenData = Depends(get_current_token_data)
):
    """
    Update the deployment meeting size.
    
    Args:
        meeting_size: The new meeting size
        token_data: JWT token data from the request
        
    Returns:
        The updated configuration
        
    Raises:
        HTTPException: If the configuration is not found or the meeting size is invalid
    """
    # Validate meeting size
    if meeting_size < 2 or meeting_size > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meeting size must be between 2 and 10"
        )
    
    # Create config service
    config_service = ConfigService()
    
    # Update the meeting size
    updated_config = await config_service.update_meeting_size(token_data.deployment_id, meeting_size)
    
    if not updated_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    
    return updated_config

@app.get("/configs", response_model=List[DeploymentConfig])
async def get_all_configs(token_data: TokenData = Depends(get_current_token_data)):
    """
    Get all deployment configurations.
    
    This endpoint is typically for administrative purposes.
    
    Args:
        token_data: JWT token data from the request
        
    Returns:
        A list of configurations
    """
    # Create config service
    config_service = ConfigService()
    
    # Get all configurations
    configs = await config_service.get_all_configs()
    
    return configs

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)