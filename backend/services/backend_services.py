import os
from fastapi import FastAPI, Depends, HTTPException, status, Form, Request, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from passlib.context import CryptContext

from backend.services.backend_auth import verify_admin, get_current_active_user, cognito_client

from backend.api.schemas.backend_models import (
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


class backend_services():
    def __init__(self):
        self.admin_username = "admin"
        self.admin_password = "admin_password"
        
    async def create_admin_user(self, db: AsyncSession):
        """This asynchronous function creates an admin user in the database if one does not already exist. 
        It checks for an existing admin user with the email "admin@busfleet.com". If none is found, 
        it creates a new User object with predefined properties, adds it to the database, and commits the changes. 
        In case of any exceptions, it rolls back the transaction and prints an error message.
        """
        try:
            # Check if admin exists
            admin = db.query(User).filter(User.email == "admin@busfleet.com").first()
            if not admin:
                admin = User(
                    email="admin@busfleet.com",
                    name="Admin User",
                    role=UserRole.ADMIN,
                    status="active"
                )
                
                db.add(admin)
                await db.commit()
                print(f"Admin user '{self.admin_username}' created.")

        except Exception as e:
            await db.rollback()
            print(f"Error creating admin user: {str(e)}")
            
            
            
    async def create_normal_user(self, user, db: AsyncSession, current_user):
        try:
            print(f"Creating user with data: {user.model_dump()}")
            print(f"Current user: {current_user.email} (role: {current_user.role})")

            # Allow both ADMIN and ADMINISTRATIVO to create users
            if current_user.role not in [UserRole.ADMIN, UserRole.ADMINISTRATIVO]:
                raise HTTPException(
                    status_code=403,
                    detail="No tiene permisos para crear usuarios"
                )

            # ADMINISTRATIVO can't create ADMIN or other ADMINISTRATIVO users
            if current_user.role == UserRole.ADMINISTRATIVO and user.role in [UserRole.ADMIN, UserRole.ADMINISTRATIVO]:
                raise HTTPException(
                    status_code=403,
                    detail="No tiene permisos para crear usuarios administrativos o administradores"
                )

            # Get company based on current user's role
            if current_user.role == UserRole.ADMIN:
                company = db.query(Company).filter(
                    Company.id == user.company_id,
                    Company.admin_id == current_user.id
                ).first()
            else:  # ADMINISTRATIVO
                company = db.query(Company).filter(
                    Company.id == current_user.company_id
                ).first()
            
            if not company:
                print(f"Company not found or access denied")
                raise HTTPException(
                    status_code=403,
                    detail="No tiene permisos para crear usuarios en esta empresa"
                )

            # Create user in Cognito
            print(f"Creating user in Cognito pool")
            try:
                cognito_response = cognito_client.admin_create_user(
                    UserPoolId=os.getenv('COGNITO_USER_POOL_ID'),
                    Username=user.email,
                    UserAttributes=[
                        {'Name': 'email', 'Value': user.email},
                        {'Name': 'email_verified', 'Value': 'true'},
                        {'Name': 'name', 'Value': user.name},
                        {'Name': 'custom:role', 'Value': user.role}
                    ],
                    TemporaryPassword='Temp@' + os.urandom(4).hex(),
                    DesiredDeliveryMediums=['EMAIL']
                )
                print(f"Cognito user created: {cognito_response['User']['Username']}")
            except Exception as e:
                print(f"Error creating Cognito user: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error creating Cognito user: {str(e)}"
                )

            # Add user to company's Cognito group
            try:
                print(f"Adding user to Cognito group: {company.cognito_group_id}")
                cognito_client.admin_add_user_to_group(
                    UserPoolId=os.getenv('COGNITO_USER_POOL_ID'),
                    Username=user.email,
                    GroupName=company.cognito_group_id
                )
            except Exception as e:
                print(f"Error adding user to Cognito group: {str(e)}")
                # Clean up Cognito user
                cognito_client.admin_delete_user(
                    UserPoolId=os.getenv('COGNITO_USER_POOL_ID'),
                    Username=user.email
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Error adding user to group: {str(e)}"
                )

            # Create user in database
            try:
                db_user = User(
                    **user.model_dump(),
                    cognito_sub=cognito_response['User']['Username']
                )
                db.add(db_user)
                db.commit()
                db.refresh(db_user)
                print(f"User created successfully: {db_user.id}")
                return db_user
            except Exception as e:
                print(f"Error creating user in database: {str(e)}")
                # Clean up Cognito
                cognito_client.admin_delete_user(
                    UserPoolId=os.getenv('COGNITO_USER_POOL_ID'),
                    Username=user.email
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Error creating user in database: {str(e)}"
                )

        except Exception as e:
            print(f"General error in create_user: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error creating user: {str(e)}"
            )