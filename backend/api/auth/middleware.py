"""Authentication middleware for the Virtual Coffee Platform."""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

from .jwt import decode_token

security = HTTPBearer()


class JWTAuthMiddleware:
    """
    Middleware for JWT token validation.
    
    This middleware can be used to protect specific routes or
    applied globally to the FastAPI application.
    """
    
    async def __call__(self, request: Request, call_next):
        """
        Process the request and validate JWT token if present.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or route handler
            
        Returns:
            Response from the next handler
            
        Raises:
            HTTPException: If token validation fails
        """
        # Skip validation for public endpoints
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)
        
        # Extract and validate token
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            # Decode and validate token
            token_data = decode_token(token)
            
            # Verify this is an access token
            if token_data.token_type != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            # Add token data to request state for use in route handlers
            request.state.token_data = token_data
            
        except (JWTError, HTTPException) as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Continue processing the request
        return await call_next(request)
    
    def _is_public_endpoint(self, path: str) -> bool:
        """
        Check if the endpoint is public (no authentication required).
        
        Args:
            path: Request path
            
        Returns:
            True if the endpoint is public, False otherwise
        """
        # List of public endpoints that don't require authentication
        public_endpoints = [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/token",
            "/auth/register",
            "/auth/refresh",
            "/auth/amazon-sso",
            "/auth/amazon",
            "/auth/google",
        ]
        
        # Check if the path matches any public endpoint
        for endpoint in public_endpoints:
            if path == endpoint or path.startswith(endpoint + "/"):
                return True
                
        return False