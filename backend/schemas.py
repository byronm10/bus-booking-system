from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from models import UserRole
from datetime import datetime

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

class CompanyCreate(BaseModel):
    name: str
    nit: str
    email: str
    phone: str
    address: str

class CompanyResponse(CompanyCreate):
    id: UUID
    cognito_group_id: str
    created_at: datetime
    status: str

    class Config:
        from_attributes = True