"""Tests for authentication functionality."""
from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from jose import jwt

from backend.api.auth.jwt import (
    ALGORITHM,
    SECRET_KEY,
    TokenPayload,
    create_access_token,
    create_refresh_token,
    create_tokens,
    decode_token,
    refresh_access_token,
)


def test_create_access_token():
    """Test creating an access token."""
    # Arrange
    user_id = "test-user-id"
    email = "test@example.com"
    deployment_id = "test-deployment"

    payload = TokenPayload(
        sub=user_id,
        email=email,
        deployment_id=deployment_id,
    )

    # Act
    token = create_access_token(payload)

    # Assert
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == user_id
    assert decoded["email"] == email
    assert decoded["deployment_id"] == deployment_id
    assert decoded["token_type"] == "access"
    assert "exp" in decoded


def test_create_refresh_token():
    """Test creating a refresh token."""
    # Arrange
    user_id = "test-user-id"
    email = "test@example.com"
    deployment_id = "test-deployment"

    payload = TokenPayload(
        sub=user_id,
        email=email,
        deployment_id=deployment_id,
    )

    # Act
    token = create_refresh_token(payload)

    # Assert
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == user_id
    assert decoded["email"] == email
    assert decoded["deployment_id"] == deployment_id
    assert decoded["token_type"] == "refresh"
    assert "exp" in decoded

    # Verify refresh token has longer expiration than access token
    refresh_exp = datetime.fromtimestamp(decoded["exp"])
    now = datetime.utcnow()
    assert refresh_exp > now + timedelta(days=1)  # At least 1 day in the future


def test_create_tokens():
    """Test creating both access and refresh tokens."""
    # Arrange
    user_id = "test-user-id"
    email = "test@example.com"
    deployment_id = "test-deployment"

    # Act
    tokens = create_tokens(user_id, email, deployment_id)

    # Assert
    assert tokens.token_type == "bearer"
    assert tokens.access_token is not None
    assert tokens.refresh_token is not None

    # Verify access token
    access_decoded = jwt.decode(tokens.access_token, SECRET_KEY, algorithms=[ALGORITHM])
    assert access_decoded["sub"] == user_id
    assert access_decoded["email"] == email
    assert access_decoded["deployment_id"] == deployment_id
    assert access_decoded["token_type"] == "access"

    # Verify refresh token
    refresh_decoded = jwt.decode(
        tokens.refresh_token, SECRET_KEY, algorithms=[ALGORITHM]
    )
    assert refresh_decoded["sub"] == user_id
    assert refresh_decoded["email"] == email
    assert refresh_decoded["deployment_id"] == deployment_id
    assert refresh_decoded["token_type"] == "refresh"


def test_decode_token_valid():
    """Test decoding a valid token."""
    # Arrange
    user_id = "test-user-id"
    email = "test@example.com"
    deployment_id = "test-deployment"

    payload = TokenPayload(
        sub=user_id,
        email=email,
        deployment_id=deployment_id,
    )

    token = create_access_token(payload)

    # Act
    token_data = decode_token(token)

    # Assert
    assert token_data.sub == user_id
    assert token_data.email == email
    assert token_data.deployment_id == deployment_id
    assert token_data.token_type == "access"
    assert token_data.exp > datetime.utcnow()


def test_decode_token_invalid():
    """Test decoding an invalid token."""
    # Arrange
    invalid_token = "invalid.token.string"

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        decode_token(invalid_token)

    assert excinfo.value.status_code == 401
    assert "Could not validate credentials" in excinfo.value.detail


def test_decode_token_missing_fields():
    """Test decoding a token with missing required fields."""
    # Arrange
    # Create a token with missing fields
    payload = {
        "sub": "test-user-id",
        # Missing email and deployment_id
        "exp": datetime.utcnow() + timedelta(minutes=15),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        decode_token(token)

    assert excinfo.value.status_code == 401
    assert "Invalid token payload" in excinfo.value.detail


def test_refresh_access_token_valid():
    """Test refreshing an access token with a valid refresh token."""
    # Arrange
    user_id = "test-user-id"
    email = "test@example.com"
    deployment_id = "test-deployment"

    # Create a refresh token
    payload = TokenPayload(
        sub=user_id,
        email=email,
        deployment_id=deployment_id,
        token_type="refresh",  # Explicitly set as refresh token
    )

    to_encode = payload.dict()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    refresh_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    # Act
    new_tokens = refresh_access_token(refresh_token)

    # Assert
    assert new_tokens.token_type == "bearer"
    assert new_tokens.refresh_token == refresh_token  # Same refresh token
    assert new_tokens.access_token != refresh_token  # New access token

    # Verify new access token
    access_decoded = jwt.decode(
        new_tokens.access_token, SECRET_KEY, algorithms=[ALGORITHM]
    )
    assert access_decoded["sub"] == user_id
    assert access_decoded["email"] == email
    assert access_decoded["deployment_id"] == deployment_id
    assert access_decoded["token_type"] == "access"


def test_refresh_access_token_with_access_token():
    """Test refreshing with an access token instead of refresh token."""
    # Arrange
    user_id = "test-user-id"
    email = "test@example.com"
    deployment_id = "test-deployment"

    payload = TokenPayload(
        sub=user_id,
        email=email,
        deployment_id=deployment_id,
    )

    access_token = create_access_token(payload)  # This is an access token, not refresh

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        refresh_access_token(access_token)

    assert excinfo.value.status_code == 401
    assert "Invalid token type for refresh operation" in excinfo.value.detail


def test_refresh_access_token_expired():
    """Test refreshing with an expired refresh token."""
    # Arrange
    user_id = "test-user-id"
    email = "test@example.com"
    deployment_id = "test-deployment"

    # Create an expired refresh token
    payload = {
        "sub": user_id,
        "email": email,
        "deployment_id": deployment_id,
        "token_type": "refresh",
        "exp": datetime.utcnow() - timedelta(days=1),  # Expired 1 day ago
    }

    expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        refresh_access_token(expired_token)

    assert excinfo.value.status_code == 401
