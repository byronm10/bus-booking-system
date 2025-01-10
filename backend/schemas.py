from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from models import UserRole
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: str
    role: UserRole
    identification: Optional[str] = None  # Make identification optional
    status: Optional[str] = "active"
    company_id: Optional[UUID] = None

class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    role: UserRole
    identification: Optional[str] = None  # Make identification optional
    status: str
    cognito_sub: Optional[str] = None
    company_id: Optional[UUID] = None
    
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