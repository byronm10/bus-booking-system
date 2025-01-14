import os
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.sdk import get_db, Base, engine
from backend.services import backend_services
from backend.services.backend_auth import verify_admin, get_current_active_user, cognito_client

from api.schemas.backend_schemas import (
    UserCreate, 
    UserResponse, 
    CompanyCreate, 
    CompanyResponse,
    VehicleCreate,
    VehicleResponse,
    RouteCreate,     # Add these
    RouteResponse,   # Add these
    RouteExecutionCreate,
    RouteExecutionResponse
)
from api.schemas.backend_models import (
    User, 
    UserRole, 
    Company, 
    Vehicle, 
    VehicleStatus,
    Route,           # Add these
    RouteStatus,     # Add these
    RouteExecution,
    RepetitionPeriod
)

router = APIRouter()

##############################################################################
#   Ambiente                                                    ##############
###############################################################################
stage = os.getenv("STAGE") if os.getenv("STAGE") else "dev"

if stage == "dev":
    print("Running in development mode -> ", stage)
#### End Ambiente ##############



# Re-insert admin user if needed
@router.on_event("startup")
async def startup_event():
    
    async with get_db() as db:  # Assuming get_db() is an async context manager
        startup_srv = backend_services()
        await startup_srv.create_admin_user(db)
        
    
    
@router.post("/users/", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    create_user_srv = backend_services()
    await create_user_srv.create_normal_user(user, db, current_user)