from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

Role = Literal["simple", "admin"]

class RegisterRequest(BaseModel):
    employee_id: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=4, max_length=72)
    role: Role = "simple"  # Only selectable at registration

class RegisterResponse(BaseModel):
    user_id: str
    employee_id: str
    role: Role
    created_at: str

class LoginRequest(BaseModel):
    employee_id: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int

class MeResponse(BaseModel):
    user_id: str
    employee_id: str
    role: Role