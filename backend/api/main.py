from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
import uvicorn

from backend.api.auth.jwt import (
    create_tokens, 
    refresh_access_token, 
    get_current_user_id,
    Token
)
from backend.api.auth.middleware import JWTAuthMiddleware

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

# Protected route example
@app.get("/users/me")
async def get_current_user(user_id: str = Depends(get_current_user_id)):
    """
    Get the current authenticated user.
    
    This is a protected route that requires a valid JWT token.
    """
    # TODO: Fetch actual user data from database
    return {"user_id": user_id, "message": "You are authenticated!"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)