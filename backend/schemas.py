from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from models import UserRole, VehicleStatus  # Add VehicleStatus here
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

class VehicleCreate(BaseModel):
    brand: str
    model: str
    year: int
    vehicle_type: str
    plate_number: str
    company_number: str
    vin: Optional[str] = None
    company_id: UUID

class VehicleResponse(VehicleCreate):
    id: UUID
    status: VehicleStatus
    created_at: datetime

    class Config:
        from_attributes = True