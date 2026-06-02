import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserRegister(BaseModel):
    """Enforces strict email formatting and minimal safety boundaries for registration inputs."""
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must contain at least 6 characters")

class UserResponse(BaseModel):
    """Filters out fields like hashed_password to ensure no leaks occur across network vectors."""
    id: uuid.UUID
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    """Standardized response payload structure for OAuth2 compliance."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Decoded internal identification structure passed through route security checkpoints."""
    user_id: uuid.UUID | None = None
