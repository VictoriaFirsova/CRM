from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole


class UserCreateAdmin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=1, max_length=255)
    role: UserRole = UserRole.MANAGER


class UserUpdateAdmin(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = Field(None, min_length=6)
