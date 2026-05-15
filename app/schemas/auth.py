from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenUserData(BaseModel):
    id:        int
    username:  str
    full_name: str
    email:     str
    role:      str

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type:   str
    user:         TokenUserData


class UserCreate(BaseModel):
    username:  str
    email:     EmailStr
    full_name: str
    password:  str
    role:      str = "almacenero"
    phone:     Optional[str] = None


class UserResponse(BaseModel):
    id:        int
    username:  str
    email:     str
    full_name: str
    role:      str
    is_active: bool
    phone:     Optional[str] = None

    model_config = {"from_attributes": True}
