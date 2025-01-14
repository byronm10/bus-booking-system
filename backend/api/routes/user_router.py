import os
from typing import List
from fastapi import FastAPI, APIRouter, HTTPException, Depends, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.sdk import get_db
from backend.services.modules.users_services import users_services_class
from backend.services.backend_auth import verify_admin, get_current_active_user

from api.schemas.backend_models import User
from api.schemas.backend_schemas import UserCreate, UserResponse


router = APIRouter()
services = users_services_class()


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
        await services.create_admin_user_srv(db)
            
    
@router.post("/users/", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    await services.create_normal_user_srv(user, db, current_user)
    
    

@router.get("/users/", response_model=List[UserResponse])
async def get_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await services.get_users_srv(db, current_user)
    


@router.put("/users/profile", response_model=UserResponse)
async def update_profile(
    user_update: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await services.update_profile_srv(user_update, db, current_user)
    
    

@router.post("/login")
async def login(username: str = Form(), password: str = Form()):
    return await services.login_srv(username, password)



@router.get("/login")
async def login_cognito(request: Request):
    return await services.login_cognito_srv(request)
    
    
@router.get("/auth") 
async def auth(request: Request, db: AsyncSession = Depends(get_db)):
    return await services.auth_srv(request, db)


@router.post("/logout")
async def logout(request: Request):
    return await services.logout_srv(request)