"""JWT Authentication middleware for token validation and user identification."""

import time
from datetime import datetime, timedelta
from typing import Callable, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import settings


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT token validation and authentication."""

    def __init__(self, app):
        super().__init__(app)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.security_scheme = HTTPBearer(auto_error=False)

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request with JWT authentication validation."""

        # Skip authentication for public endpoints
        public_endpoints = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/",
            "/test"
        ]

        if any(request.url.path.startswith(endpoint) for endpoint in public_endpoints):
            return await call_next(request)

        # Extract token from Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "AUTHENTICATION_REQUIRED",
                    "message": "Authentication token required",
                    "timestamp": time.time()
                }
            )

        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "INVALID_AUTH_SCHEME",
                        "message": "Authorization scheme must be Bearer",
                        "timestamp": time.time()
                    }
                )
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "INVALID_AUTH_FORMAT",
                    "message": "Authorization header must be in format 'Bearer <token>'",
                    "timestamp": time.time()
                }
            )

        # Validate JWT token
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )

            # Check token expiration
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                exp_datetime = datetime.fromtimestamp(exp_timestamp)
                if datetime.utcnow() > exp_datetime:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={
                            "error": "TOKEN_EXPIRED",
                            "message": "Authentication token has expired",
                            "timestamp": time.time()
                        }
                    )

            # Add agent info to request state
            request.state.agent_id = payload.get("sub")
            request.state.agent_role = payload.get("role", "agent")
            request.state.token_payload = payload

        except JWTError as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "INVALID_TOKEN",
                    "message": f"Token validation failed: {str(e)}",
                    "timestamp": time.time()
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "AUTHENTICATION_ERROR",
                    "message": f"Authentication system error: {str(e)}",
                    "timestamp": time.time()
                }
            )

        # Continue with authenticated request
        response = await call_next(request)
        return response


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)


# FastAPI dependency for getting current agent
def get_current_agent(request: Request):
    """Get current authenticated agent from request."""
    if not hasattr(request.state, "agent_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    # Import here to avoid circular imports
    from src.models.agent import Agent

    agent_id = request.state.agent_id
    return Agent(
        id=agent_id,
        name=f"Agent {agent_id}",
        type="clearing",
        contactInfo={
            "phone": "+234-123-4567",
            "email": f"{agent_id}@efl.com",
            "companyName": "EFL Agency"
        },
        permissions=[
            {"resource": "container", "actions": ["read", "track", "write"]},
            {"resource": "bl", "actions": ["read", "track", "write"]},
            {"resource": "session", "actions": ["read", "write", "manage"]},
            {"resource": "voice", "actions": ["read", "write"]},
            {"resource": "chat", "actions": ["read", "write"]}
        ],
        sessionHistory=[],
        companyName="EFL Agency"
    )


# Optional dependency for endpoints that can work with or without auth
def get_current_agent_optional(request: Request) -> Optional[dict]:
    """Get current authenticated agent if available."""
    if hasattr(request.state, "agent_id"):
        return {
            "agent_id": request.state.agent_id,
            "role": request.state.agent_role,
            "token_payload": request.state.token_payload
        }
    return None
