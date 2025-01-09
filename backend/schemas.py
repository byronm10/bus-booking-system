from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from models import UserRole

class UserCreate(BaseModel):
    name: str
    email: str
    role: UserRole
    status: Optional[str] = "active"

class UserResponse(UserCreate):
    id: UUID
    cognito_sub: Optional[str] = None  # Make cognito_sub optional
    
    class Config:
        from_attributes = True