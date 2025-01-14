import os

from passlib.context import CryptContext
from fastapi import FastAPI, Depends, HTTPException, status, Form, Request, Body
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

from starlette.config import Config
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth


from backend.services.backend_auth import verify_admin, get_current_active_user, cognito_client
from backend.api.schemas.backend_models import (
    User, 
    UserRole, 
    Company
)


# Configure OAuth
config = Config('.env')
oauth = OAuth(config)

oauth.register(
    name='cognito',
    server_metadata_url=f"https://cognito-idp.{os.getenv('AWS_REGION')}.amazonaws.com/{os.getenv('COGNITO_USER_POOL_ID')}/.well-known/openid-configuration",
    client_id=os.getenv('COGNITO_APP_CLIENT_ID'),
    client_secret=os.getenv('COGNITO_APP_CLIENT_SECRET'),
    client_kwargs={
        'scope': 'email openid phone aws.cognito.signin.user.admin',
        'redirect_uri': 'http://localhost:8000/auth'
    }
)


class companies_services_class():
    
    async def create_company_srv(self, company, db, current_user):
        """This asynchronous function creates a company in the database and a corresponding group in AWS Cognito. 
        It first checks if the current user has admin privileges. If so, it creates a group for the company in Cognito, 
        adds the current user to that group, and then creates a company record in the database. 
        If any errors occur during this process, it attempts to delete the created group and rolls back the database transaction."""

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
            await db.commit()
            
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
            
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        
        
    async def get_companies_srv(self, db, current_user):
        """This asynchronous function retrieves companies associated with the current user from the database. 
        It filters the companies based on the admin ID of the current user and 
        handles any exceptions that may occur during the database query."""

        try:
            # Cada admin solo ve sus propias empresas
            companies = (
                db.query(Company)
                .filter(Company.admin_id == current_user.id)
                .all()
            )
            print(f"Filtering companies for user {current_user.id} with email {current_user.email}")
            print(f"Found {len(companies)} companies")
            
            return companies
        except Exception as e:
            print(f"Error fetching companies: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error fetching companies: {str(e)}"
            )