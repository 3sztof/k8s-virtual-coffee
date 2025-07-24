"""JWT token management utilities for the Virtual Coffee Platform."""
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr

# Configuration constants
# In production, these should be loaded from environment variables or a secure configuration
SECRET_KEY = "REPLACE_WITH_SECURE_SECRET_KEY_IN_PRODUCTION"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# OAuth2 scheme for token extraction from requests
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


class Token(BaseModel):
    """Token response model."""

    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data model for decoded JWT payload."""

    sub: str  # User ID
    email: EmailStr
    deployment_id: str
    exp: datetime
    token_type: str


class TokenPayload(BaseModel):
    """Token payload model for JWT creation."""

    sub: str  # User ID
    email: EmailStr
    deployment_id: str
    token_type: str = "access"


def create_access_token(data: TokenPayload) -> str:
    """
    Create a new JWT access token.

    Args:
        data: Token payload data

    Returns:
        Encoded JWT token string
    """
    to_encode = data.dict()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: TokenPayload) -> str:
    """
    Create a new JWT refresh token with longer expiration.

    Args:
        data: Token payload data

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.dict()
    to_encode["token_type"] = "refresh"
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_tokens(user_id: str, email: str, deployment_id: str) -> Token:
    """
    Create both access and refresh tokens for a user.

    Args:
        user_id: User ID
        email: User email
        deployment_id: Deployment ID

    Returns:
        Token object containing access and refresh tokens
    """
    token_payload = TokenPayload(
        sub=user_id,
        email=email,
        deployment_id=deployment_id,
    )

    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenData object with decoded payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Extract required fields
        user_id = payload.get("sub")
        email = payload.get("email")
        deployment_id = payload.get("deployment_id")
        exp = payload.get("exp")
        token_type = payload.get("token_type")

        if user_id is None or email is None or deployment_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Convert exp to datetime
        exp_datetime = datetime.fromtimestamp(exp)

        return TokenData(
            sub=user_id,
            email=email,
            deployment_id=deployment_id,
            exp=exp_datetime,
            token_type=token_type,
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def refresh_access_token(refresh_token: str) -> Token:
    """
    Create a new access token using a valid refresh token.

    Args:
        refresh_token: Valid refresh token

    Returns:
        Token object with new access token and the same refresh token

    Raises:
        HTTPException: If refresh token is invalid, expired, or not a refresh token
    """
    token_data = decode_token(refresh_token)

    # Verify this is a refresh token
    if token_data.token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type for refresh operation",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create a new access token
    token_payload = TokenPayload(
        sub=token_data.sub,
        email=token_data.email,
        deployment_id=token_data.deployment_id,
    )

    new_access_token = create_access_token(token_payload)

    return Token(
        access_token=new_access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


async def get_current_token_data(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    Dependency to get the current token data from a request.

    Args:
        token: JWT token extracted from request

    Returns:
        TokenData object with decoded payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    return decode_token(token)


async def get_current_user_id(
    token_data: TokenData = Depends(get_current_token_data)
) -> str:
    """
    Dependency to get the current user ID from a request.

    Args:
        token_data: Decoded token data

    Returns:
        User ID string

    Raises:
        HTTPException: If token is not an access token
    """
    # Verify this is an access token
    if token_data.token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_data.sub
