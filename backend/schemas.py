from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from models import UserRole, VehicleStatus, RouteStatus, RepetitionPeriod  # Add RouteStatus and RepetitionPeriod here
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

class IntermediateStop(BaseModel):
    location: str
    coordinates: Optional[dict] = None
    estimated_stop_time: int  # minutes

class RouteCreate(BaseModel):
    name: str
    start_point: str
    end_point: str
    intermediate_stops: List[IntermediateStop] = []
    departure_time: datetime
    estimated_duration: int
    repetition_frequency: Optional[int] = None
    repetition_period: Optional[str] = None
    company_id: UUID
    vehicle_id: Optional[UUID] = None  # Optional manual vehicle assignment

class RouteResponse(RouteCreate):
    id: UUID
    status: RouteStatus
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class RouteExecutionCreate(BaseModel):
    route_id: UUID
    vehicle_id: UUID
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    actual_duration: Optional[int] = None
    incidents: Optional[List[dict]] = None

class RouteExecutionResponse(RouteExecutionCreate):
    id: UUID
    status: RouteStatus
    created_at: datetime

    class Config:
        from_attributes = True