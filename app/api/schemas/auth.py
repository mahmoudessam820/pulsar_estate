from pydantic import BaseModel, EmailStr, Field, field_validator


# Request Schemas
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    def password_strength(cls, value):
        if not any(char.isupper() for char in value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isalpha() for char in value):
            raise ValueError("Password must contain at least one letter")
        return value


class loginRequest(BaseModel):
    email: EmailStr
    password: str


# Response Schemas
class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserPublic"  # Forward reference


class UserPublic(BaseModel):
    id: str
    email: EmailStr
    is_active: bool

    class Config:
        from_attributes = True


# Token Payload (internal)
class TokenPayload(BaseModel):
    sub: int  # user id
    exp: int
