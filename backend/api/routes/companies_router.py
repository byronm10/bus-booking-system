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





@router.post("/companies/", response_model=CompanyResponse)
async def create_company(
    company: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)  # Cambiado de verify_admin
):
    try:
        # Verificar que el usuario es ADMIN
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=403,
                detail="Solo los administradores pueden crear empresas"
            )

        # Crear grupo en Cognito usando el nombre de la empresa
        group_name = company.name.lower().replace(" ", "_")
        cognito_response = cognito_client.create_group(
            GroupName=group_name,
            UserPoolId=os.getenv('COGNITO_USER_POOL_ID'),
            Description=f"Grupo para la empresa de transporte: {company.name}"
        )

        # Agregar admin al grupo en Cognito
        cognito_client.admin_add_user_to_group(
            UserPoolId=os.getenv('COGNITO_USER_POOL_ID'),
            Username=current_user.email,  # Usar el email del usuario actual
            GroupName=group_name
        )

        # Crear la empresa en la base de datos
        db_company = Company(
            **company.model_dump(),
            cognito_group_id=cognito_response['Group']['GroupName'],
            admin_id=current_user.id  # Usar el ID del usuario actual
        )
        
        db.add(db_company)
        db.commit()
        db.refresh(db_company)
        return db_company

    except Exception as e:
        print(f"Error creating company: {str(e)}")  # Añadido para debugging
        # Rollback en caso de error
        try:
            if 'group_name' in locals():
                cognito_client.delete_group(
                    GroupName=group_name,
                    UserPoolId=os.getenv('COGNITO_USER_POOL_ID')
                )
        except:
            pass
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))