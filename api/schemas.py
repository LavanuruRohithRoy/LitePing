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

class MonitorCreate(BaseModel):
    """Validates incoming target monitor configuration payloads."""
    name: str = Field(..., max_length=100, description="Friendly descriptive name for the target")
    monitor_type: str = Field("HTTP", description="Type of check: 'HTTP' or 'CRON'")
    target_url: str | None = Field(None, max_length=512, description="Target URL for HTTP checks")
    check_interval_seconds: int = Field(60, ge=10, le=86400, description="Interval window from 10s to 1 day")

class MonitorResponse(BaseModel):
    """Serialized network output shape for monitor configurations."""
    id: uuid.UUID
    name: str
    monitor_type: str
    target_url: str | None
    check_interval_seconds: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class PingLogResponse(BaseModel):
    """Serialized network output shape for chronological infrastructure tracking charts."""
    id: int
    status_code: int | None
    response_time_ms: int | None
    is_up: bool
    error_message: str | None
    checked_at: datetime

    class Config:
        from_attributes = True

