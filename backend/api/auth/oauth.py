"""OAuth integration for federated authentication providers."""
import secrets
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from pydantic import BaseModel

# Configuration constants
# In production, these should be loaded from environment variables or a secure configuration

# Amazon Internal SSO (for employees)
AMAZON_SSO_CLIENT_ID = "REPLACE_WITH_AMAZON_SSO_CLIENT_ID"
AMAZON_SSO_CLIENT_SECRET = "REPLACE_WITH_AMAZON_SSO_CLIENT_SECRET"
AMAZON_SSO_AUTHORIZE_URL = "https://sso.amazon.com/oauth2/authorize"
AMAZON_SSO_TOKEN_URL = "https://sso.amazon.com/oauth2/token"
AMAZON_SSO_USERINFO_URL = "https://sso.amazon.com/oauth2/userInfo"

# Amazon Public OAuth
AMAZON_PUBLIC_CLIENT_ID = "REPLACE_WITH_AMAZON_PUBLIC_CLIENT_ID"
AMAZON_PUBLIC_CLIENT_SECRET = "REPLACE_WITH_AMAZON_PUBLIC_CLIENT_SECRET"
AMAZON_PUBLIC_AUTHORIZE_URL = "https://www.amazon.com/ap/oa"
AMAZON_PUBLIC_TOKEN_URL = "https://api.amazon.com/auth/o2/token"
AMAZON_PUBLIC_USERINFO_URL = "https://api.amazon.com/user/profile"

# Google OAuth
GOOGLE_CLIENT_ID = "REPLACE_WITH_GOOGLE_CLIENT_ID"
GOOGLE_CLIENT_SECRET = "REPLACE_WITH_GOOGLE_CLIENT_SECRET"
GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

# Store for state parameters to prevent CSRF attacks
# In production, this should be replaced with a proper storage solution (e.g., Redis)
STATE_STORE: dict[str, str] = {}


class OAuthProvider(BaseModel):
    """OAuth provider configuration."""

    name: str
    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    scopes: list[str]
    redirect_uri: str = ""  # Will be set dynamically


# OAuth provider configurations
PROVIDERS = {
    "amazon-sso": OAuthProvider(
        name="Amazon SSO (Internal)",
        client_id=AMAZON_SSO_CLIENT_ID,
        client_secret=AMAZON_SSO_CLIENT_SECRET,
        authorize_url=AMAZON_SSO_AUTHORIZE_URL,
        token_url=AMAZON_SSO_TOKEN_URL,
        userinfo_url=AMAZON_SSO_USERINFO_URL,
        scopes=["openid", "profile", "email"],
    ),
    "amazon": OAuthProvider(
        name="Amazon",
        client_id=AMAZON_PUBLIC_CLIENT_ID,
        client_secret=AMAZON_PUBLIC_CLIENT_SECRET,
        authorize_url=AMAZON_PUBLIC_AUTHORIZE_URL,
        token_url=AMAZON_PUBLIC_TOKEN_URL,
        userinfo_url=AMAZON_PUBLIC_USERINFO_URL,
        scopes=["profile", "profile:user_id", "profile:email"],
    ),
    "google": OAuthProvider(
        name="Google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        authorize_url=GOOGLE_AUTHORIZE_URL,
        token_url=GOOGLE_TOKEN_URL,
        userinfo_url=GOOGLE_USERINFO_URL,
        scopes=["openid", "profile", "email"],
    ),
}


class OAuthUserInfo(BaseModel):
    """User information from OAuth provider."""

    provider: str
    provider_user_id: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None


def generate_authorization_url(
    provider_id: str, base_url: str, deployment_id: str
) -> str:
    """
    Generate the authorization URL for the specified OAuth provider.

    Args:
        provider_id: OAuth provider ID
        base_url: Base URL of the application for constructing the redirect URI
        deployment_id: Deployment ID for multi-tenant support

    Returns:
        Authorization URL for the OAuth provider

    Raises:
        HTTPException: If the provider ID is invalid
    """
    if provider_id not in PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OAuth provider: {provider_id}",
        )

    provider = PROVIDERS[provider_id]

    # Set the redirect URI
    provider.redirect_uri = f"{base_url}/auth/{provider_id}/callback"

    # Generate a random state parameter to prevent CSRF attacks
    state = secrets.token_urlsafe(32)

    # Store the state parameter with the deployment ID
    STATE_STORE[state] = deployment_id

    # Build the authorization URL
    params = {
        "client_id": provider.client_id,
        "redirect_uri": provider.redirect_uri,
        "response_type": "code",
        "scope": " ".join(provider.scopes),
        "state": state,
    }

    return f"{provider.authorize_url}?{urlencode(params)}"


async def handle_oauth_callback(
    provider_id: str, code: str, state: str
) -> OAuthUserInfo:
    """
    Handle the OAuth callback from the provider.

    Args:
        provider_id: OAuth provider ID
        code: Authorization code from the provider
        state: State parameter from the provider

    Returns:
        User information from the OAuth provider

    Raises:
        HTTPException: If the provider ID is invalid or the state is invalid
    """
    if provider_id not in PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OAuth provider: {provider_id}",
        )

    # Verify the state parameter to prevent CSRF attacks
    if state not in STATE_STORE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter",
        )

    # Get the deployment ID from the state store
    deployment_id = STATE_STORE[state]

    # Remove the state parameter from the store
    del STATE_STORE[state]

    provider = PROVIDERS[provider_id]

    # Exchange the authorization code for an access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            provider.token_url,
            data={
                "client_id": provider.client_id,
                "client_secret": provider.client_secret,
                "code": code,
                "redirect_uri": provider.redirect_uri,
                "grant_type": "authorization_code",
            },
        )

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Failed to get access token: {token_response.text}",
            )

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No access token in response",
            )

        # Get user information from the provider
        userinfo_response = await client.get(
            provider.userinfo_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if userinfo_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Failed to get user info: {userinfo_response.text}",
            )

        userinfo_data = userinfo_response.json()

        # Extract user information based on the provider
        if provider_id == "amazon-sso":
            # Amazon internal SSO for employees
            return OAuthUserInfo(
                provider=provider_id,
                provider_user_id=userinfo_data.get("sub"),
                email=userinfo_data.get("email"),
                name=userinfo_data.get("name"),
                picture=userinfo_data.get("picture"),
            )
        elif provider_id == "amazon":
            # Amazon public OAuth
            return OAuthUserInfo(
                provider=provider_id,
                provider_user_id=userinfo_data.get("user_id"),
                email=userinfo_data.get("email"),
                name=userinfo_data.get("name"),
                picture=None,  # Amazon public OAuth doesn't provide a picture
            )
        elif provider_id == "google":
            # Google OAuth
            return OAuthUserInfo(
                provider=provider_id,
                provider_user_id=userinfo_data.get("sub"),
                email=userinfo_data.get("email"),
                name=userinfo_data.get("name"),
                picture=userinfo_data.get("picture"),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {provider_id}",
            )


def get_deployment_id_from_state(state: str) -> str:
    """
    Get the deployment ID from the state parameter.

    Args:
        state: State parameter from the OAuth provider

    Returns:
        Deployment ID associated with the state

    Raises:
        HTTPException: If the state parameter is invalid
    """
    if state not in STATE_STORE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter",
        )

    return STATE_STORE[state]
