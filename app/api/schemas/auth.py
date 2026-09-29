from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


# Request Schemas
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if not any(char.isupper() for char in value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isalpha() for char in value):
            raise ValueError("Password must contain at least one letter")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# Response Schemas
class UserPublic(BaseModel):
    id: UUID
    email: EmailStr
    is_active: bool

    """
    Pydantic's from_attributes=True reads the SQLAlchemy object, 
    and its built-in type coercion automatically converts the uuid.UUID to a str and datetime to an ISO string.
    """
    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic  # Forward reference

    model_config = ConfigDict(from_attributes=True)


# Token Payload (internal)
class TokenPayload(BaseModel):
    sub: str  # user id
    exp: int
