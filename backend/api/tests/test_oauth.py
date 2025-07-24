"""Integration tests for OAuth authentication flows."""
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from backend.api.auth.oauth import (
    STATE_STORE,
    OAuthUserInfo,
    generate_authorization_url,
    handle_oauth_callback,
)
from backend.api.main import app


@pytest.fixture()
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


def test_oauth_login_amazon_sso(client):
    """Test initiating OAuth login with Amazon SSO."""
    # Mock the generate_authorization_url function
    with patch("backend.api.auth.oauth.generate_authorization_url") as mock_gen_url:
        # Set up the mock to return a known URL
        mock_gen_url.return_value = "https://sso.amazon.com/oauth2/authorize?mock=true"

        # Make the request to the OAuth login endpoint
        response = client.get("/auth/amazon-sso", allow_redirects=False)

        # Verify the response is a redirect
        assert response.status_code == 307
        assert (
            response.headers["location"]
            == "https://sso.amazon.com/oauth2/authorize?mock=true"
        )

        # Verify the generate_authorization_url function was called with the correct arguments
        mock_gen_url.assert_called_once()
        args = mock_gen_url.call_args[0]
        assert args[0] == "amazon-sso"
        assert "http" in args[1]  # Base URL should contain http


def test_oauth_login_amazon(client):
    """Test initiating OAuth login with Amazon public OAuth."""
    # Mock the generate_authorization_url function
    with patch("backend.api.auth.oauth.generate_authorization_url") as mock_gen_url:
        # Set up the mock to return a known URL
        mock_gen_url.return_value = "https://www.amazon.com/ap/oa?mock=true"

        # Make the request to the OAuth login endpoint
        response = client.get("/auth/amazon", allow_redirects=False)

        # Verify the response is a redirect
        assert response.status_code == 307
        assert response.headers["location"] == "https://www.amazon.com/ap/oa?mock=true"

        # Verify the generate_authorization_url function was called with the correct arguments
        mock_gen_url.assert_called_once()
        args = mock_gen_url.call_args[0]
        assert args[0] == "amazon"
        assert "http" in args[1]  # Base URL should contain http


def test_oauth_login_google(client):
    """Test initiating OAuth login with Google OAuth."""
    # Mock the generate_authorization_url function
    with patch("backend.api.auth.oauth.generate_authorization_url") as mock_gen_url:
        # Set up the mock to return a known URL
        mock_gen_url.return_value = (
            "https://accounts.google.com/o/oauth2/auth?mock=true"
        )

        # Make the request to the OAuth login endpoint
        response = client.get("/auth/google", allow_redirects=False)

        # Verify the response is a redirect
        assert response.status_code == 307
        assert (
            response.headers["location"]
            == "https://accounts.google.com/o/oauth2/auth?mock=true"
        )

        # Verify the generate_authorization_url function was called with the correct arguments
        mock_gen_url.assert_called_once()
        args = mock_gen_url.call_args[0]
        assert args[0] == "google"
        assert "http" in args[1]  # Base URL should contain http


def test_oauth_callback_amazon_sso(client):
    """Test handling OAuth callback from Amazon SSO."""
    # Mock the handle_oauth_callback function
    with patch("backend.api.main.handle_oauth_callback") as mock_handle_callback, patch(
        "backend.api.main.get_deployment_id_from_state"
    ) as mock_get_deployment_id:
        # Set up the mocks
        mock_user_info = OAuthUserInfo(
            provider="amazon-sso",
            provider_user_id="test-user-id",
            email="test@amazon.com",
            name="Test User",
            picture="https://example.com/picture.jpg",
        )
        mock_handle_callback.return_value = mock_user_info
        mock_get_deployment_id.return_value = "test-deployment"

        # Add a test state to the STATE_STORE
        test_state = "test-state"
        STATE_STORE[test_state] = "test-deployment"

        # Make the request to the OAuth callback endpoint
        response = client.get(
            f"/auth/amazon-sso/callback?code=test-code&state={test_state}"
        )

        # Verify the response contains the expected HTML
        assert response.status_code == 200
        assert "Authentication Successful" in response.text
        assert "amazon-sso" in response.text
        assert "access_token" in response.text
        assert "refresh_token" in response.text

        # Verify the handle_oauth_callback function was called with the correct arguments
        mock_handle_callback.assert_called_once_with(
            "amazon-sso", "test-code", test_state
        )
        mock_get_deployment_id.assert_called_once_with(test_state)


def test_oauth_callback_amazon(client):
    """Test handling OAuth callback from Amazon public OAuth."""
    # Mock the handle_oauth_callback function
    with patch("backend.api.main.handle_oauth_callback") as mock_handle_callback, patch(
        "backend.api.main.get_deployment_id_from_state"
    ) as mock_get_deployment_id:
        # Set up the mocks
        mock_user_info = OAuthUserInfo(
            provider="amazon",
            provider_user_id="amzn1.account.TEST",
            email="test@example.com",
            name="Test User",
            picture=None,
        )
        mock_handle_callback.return_value = mock_user_info
        mock_get_deployment_id.return_value = "test-deployment"

        # Add a test state to the STATE_STORE
        test_state = "test-state-amazon"
        STATE_STORE[test_state] = "test-deployment"

        # Make the request to the OAuth callback endpoint
        response = client.get(
            f"/auth/amazon/callback?code=test-code&state={test_state}"
        )

        # Verify the response contains the expected HTML
        assert response.status_code == 200
        assert "Authentication Successful" in response.text
        assert "amazon" in response.text
        assert "access_token" in response.text
        assert "refresh_token" in response.text

        # Verify the handle_oauth_callback function was called with the correct arguments
        mock_handle_callback.assert_called_once_with("amazon", "test-code", test_state)
        mock_get_deployment_id.assert_called_once_with(test_state)


def test_oauth_callback_google(client):
    """Test handling OAuth callback from Google OAuth."""
    # Mock the handle_oauth_callback function
    with patch("backend.api.main.handle_oauth_callback") as mock_handle_callback, patch(
        "backend.api.main.get_deployment_id_from_state"
    ) as mock_get_deployment_id:
        # Set up the mocks
        mock_user_info = OAuthUserInfo(
            provider="google",
            provider_user_id="123456789",
            email="test@gmail.com",
            name="Test User",
            picture="https://example.com/picture.jpg",
        )
        mock_handle_callback.return_value = mock_user_info
        mock_get_deployment_id.return_value = "test-deployment"

        # Add a test state to the STATE_STORE
        test_state = "test-state-google"
        STATE_STORE[test_state] = "test-deployment"

        # Make the request to the OAuth callback endpoint
        response = client.get(
            f"/auth/google/callback?code=test-code&state={test_state}"
        )

        # Verify the response contains the expected HTML
        assert response.status_code == 200
        assert "Authentication Successful" in response.text
        assert "google" in response.text
        assert "access_token" in response.text
        assert "refresh_token" in response.text

        # Verify the handle_oauth_callback function was called with the correct arguments
        mock_handle_callback.assert_called_once_with("google", "test-code", test_state)
        mock_get_deployment_id.assert_called_once_with(test_state)


def test_oauth_callback_error(client):
    """Test handling OAuth callback with an error."""
    # Mock the handle_oauth_callback function to raise an exception
    with patch("backend.api.main.handle_oauth_callback") as mock_handle_callback:
        from fastapi import HTTPException

        mock_handle_callback.side_effect = HTTPException(
            status_code=400,
            detail="Invalid state parameter",
        )

        # Make the request to the OAuth callback endpoint
        response = client.get(
            "/auth/google/callback?code=test-code&state=invalid-state"
        )

        # Verify the response contains the expected error HTML
        assert response.status_code == 400
        assert "Authentication Error" in response.text
        assert "Invalid state parameter" in response.text
        assert "400" in response.text

        # Verify the handle_oauth_callback function was called with the correct arguments
        mock_handle_callback.assert_called_once_with(
            "google", "test-code", "invalid-state"
        )


def test_generate_authorization_url():
    """Test generating an authorization URL."""
    # Call the function directly
    url = generate_authorization_url(
        "google", "http://localhost:8000", "test-deployment"
    )

    # Parse the URL to verify its components
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    # Verify the URL components
    assert parsed_url.scheme == "https"
    assert parsed_url.netloc == "accounts.google.com"
    assert parsed_url.path == "/o/oauth2/auth"
    assert "client_id" in query_params
    assert "redirect_uri" in query_params
    assert "response_type" in query_params
    assert "scope" in query_params
    assert "state" in query_params
    assert query_params["response_type"][0] == "code"

    # Verify the state parameter was stored
    state = query_params["state"][0]
    assert state in STATE_STORE
    assert STATE_STORE[state] == "test-deployment"


@pytest.mark.asyncio()
async def test_handle_oauth_callback():
    """Test handling an OAuth callback."""
    # Mock the httpx.AsyncClient
    with patch("httpx.AsyncClient") as mock_client:
        # Set up the mock client
        mock_response_token = MagicMock()
        mock_response_token.status_code = 200
        mock_response_token.json.return_value = {
            "access_token": "mock-access-token",
            "token_type": "bearer",
            "expires_in": 3600,
        }

        mock_response_userinfo = MagicMock()
        mock_response_userinfo.status_code = 200
        mock_response_userinfo.json.return_value = {
            "sub": "123456789",
            "email": "test@gmail.com",
            "name": "Test User",
            "picture": "https://example.com/picture.jpg",
        }

        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response_token
        mock_client_instance.get.return_value = mock_response_userinfo
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Add a test state to the STATE_STORE
        test_state = "test-state-callback"
        STATE_STORE[test_state] = "test-deployment"

        # Call the function
        user_info = await handle_oauth_callback("google", "test-code", test_state)

        # Verify the user info
        assert user_info.provider == "google"
        assert user_info.provider_user_id == "123456789"
        assert user_info.email == "test@gmail.com"
        assert user_info.name == "Test User"
        assert user_info.picture == "https://example.com/picture.jpg"

        # Verify the state was removed from the store
        assert test_state not in STATE_STORE

        # Verify the httpx client was called correctly
        mock_client_instance.post.assert_called_once()
        mock_client_instance.get.assert_called_once()

        # Verify the token request
        token_call = mock_client_instance.post.call_args
        assert token_call[0][0].endswith("/token")
        assert "code" in token_call[1]["data"]
        assert token_call[1]["data"]["code"] == "test-code"
        assert "grant_type" in token_call[1]["data"]
        assert token_call[1]["data"]["grant_type"] == "authorization_code"

        # Verify the userinfo request
        userinfo_call = mock_client_instance.get.call_args
        assert userinfo_call[0][0].endswith("/userinfo")
        assert "Authorization" in userinfo_call[1]["headers"]
        assert (
            userinfo_call[1]["headers"]["Authorization"] == "Bearer mock-access-token"
        )
