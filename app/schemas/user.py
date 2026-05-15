from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username:  str
    email:     EmailStr
    full_name: str
    role:      str = "almacenero"
    phone:     Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email:     Optional[EmailStr] = None
    full_name: Optional[str]     = None
    phone:     Optional[str]     = None
    role:      Optional[str]     = None
    is_active: Optional[bool]    = None


class UserChangePassword(BaseModel):
    current_password: str
    new_password:     str


class UserResponse(UserBase):
    id:             int
    is_active:      bool
    created_at:     datetime
    updated_at:     Optional[datetime] = None
    last_login:     Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    total: int
    items: list[UserResponse]
