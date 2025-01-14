import os
from typing import List
from fastapi import FastAPI, APIRouter, HTTPException, Depends, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.sdk import get_db, Base, engine
from backend.services.backend_auth import verify_admin, get_current_active_user
from backend.services.modules.companies_services import companies_services_class

from api.schemas.backend_schemas import (
    CompanyCreate, 
    CompanyResponse
)
from api.schemas.backend_models import (
    User, 
    UserRole, 
    Company
)

router = APIRouter()
services = companies_services_class()


##############################################################################
#   Ambiente                                                    ##############
###############################################################################
stage = os.getenv("STAGE") if os.getenv("STAGE") else "dev"

if stage == "dev":
    print("Running in development mode -> ", stage)
#### End Ambiente ##############





@router.post("/newcompany/", response_model=CompanyResponse)
async def create_company(
    company: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)  # Cambiado de verify_admin
):
    return await services.create_company_srv(company, db, current_user)



@router.get("/companies/", response_model=List[CompanyResponse])
async def get_companies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await services.get_companies_srv(db, current_user)