"""
api/auth/routes.py
------------------
Authentication endpoints: register, login, and current user.
Replace the stub implementations with real DB + JWT logic.
"""

from uuid import uuid4

from fastapi import APIRouter, HTTPException

from api.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from core.config import settings

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

# Temporary in-memory user store — replace with DB calls
_USERS: dict[str, dict] = {}


@auth_router.post("/register", response_model=UserResponse, status_code=201)
def register(payload: RegisterRequest):
    """Register a new user."""
    if any(u["email"] == payload.email for u in _USERS.values()):
        raise HTTPException(status_code=409, detail="Email already registered")

    user_id = str(uuid4())
    _USERS[user_id] = {
        "id": user_id,
        "email": payload.email,
        "full_name": payload.full_name,
        # TODO: hash password before storing
        "password_hash": payload.password,
    }
    return UserResponse(**_USERS[user_id])


@auth_router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    """Authenticate and return a JWT access token."""
    user = next((u for u in _USERS.values() if u["email"] == payload.email), None)
    if not user or user["password_hash"] != payload.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # TODO: generate a real JWT using settings.secret_key + settings.algorithm
    fake_token = f"fake-jwt-for-{user['id']}"
    return TokenResponse(
        access_token=fake_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )
