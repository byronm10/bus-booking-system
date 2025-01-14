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
    Company, 
    Vehicle, 
    VehicleStatus,
    Route,           # Add these
    RouteStatus,     # Add these
    RouteExecution,
    RepetitionPeriod
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


class users_services_class():
    def __init__(self):
        self.admin_username = "admin"
        self.admin_password = "admin_password"
        
    async def create_admin_user_srv(self, db: AsyncSession):
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
            
            
            
    async def create_normal_user_srv(self, user, db: AsyncSession, current_user):
        """ This asynchronous function creates a normal user in a system,
            ensuring that the current user has the appropriate permissions based on their role.
            It first validates the user's role and checks if they have permission to create users in
            the specified company. If valid, it creates the user in AWS Cognito and adds them to
            the corresponding Cognito group. Finally, it creates the user in the local database,
            handling any errors that may occur during the process and
            performing necessary clean-up in case of failures.

            Args:
                user (_type_): _description_
                db (AsyncSession): _description_
                current_user (_type_): _description_

            Raises:
                HTTPException: _description_
                HTTPException: _description_
                HTTPException: _description_
                HTTPException: _description_
                HTTPException: _description_
                HTTPException: _description_
                HTTPException: _description_

            Returns:
                _type_: _description_
        """
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
                user_data = user.model_dump()  # Assuming this is necessary
                db_user = User(
                    **user_data,
                    cognito_sub=cognito_response['User']['Username']
                )
                
                db.add(db_user)
                await db.commit()
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
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error creating user: {str(e)}"
            )
            
            

    async def get_users_srv(self, db: AsyncSession, current_user):
        """This asynchronous function retrieves users associated with companies administered by the current user. 
        It queries the database for companies linked to the current user's ID, extracts their IDs, 
        and then retrieves users belonging to those companies. In case of an error, it rolls back the database session 
        and raises an HTTPException with an appropriate error message.
        """

        try:
            # Get companies administered by current user
            admin_companies = db.query(Company).filter(
                Company.admin_id == current_user.id
            ).all()
            
            # Get company IDs administered by current user
            company_ids = [company.id for company in admin_companies]
            
            # Get users belonging to those companies
            users = db.query(User).filter(User.company_id.in_(company_ids)).all()
            return users
    
        except Exception as e:
            print(f"General error getting users: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error getting users: {str(e)}"
            )
            
            
            
    async def update_profile_srv(self, user_update, db: AsyncSession, current_user):
        """This asynchronous function updates the profile of a user in the system.
        It first checks if the user is trying to change their email address, and if so,
        it updates the Cognito user pool and the local database. If any errors occur during the process,
        it rolls back the database session and raises an HTTPException with an appropriate error message.
        """

        print(f"Updating profile for user: {current_user.email} (role: {current_user.role})")
        
        try:
            # Check if email is being changed
            email_changed = user_update.email != current_user.email

            # Update Cognito user
            cognito_client.admin_update_user_attributes(
                UserPoolId=os.getenv('COGNITO_USER_POOL_ID'),
                Username=current_user.email,
                UserAttributes=[
                    {'Name': 'email', 'Value': user_update.email},
                    {'Name': 'name', 'Value': user_update.name}
                ]
            )

            # Update database user
            for key, value in user_update.model_dump().items():
                if key != 'role':  # Don't allow role changes through profile update
                    setattr(current_user, key, value)

            db.commit()
            db.refresh(current_user)
            
            # Return response with warning if email changed
            response_data = current_user
            if email_changed:
                return JSONResponse(
                    content={
                        "user": jsonable_encoder(response_data),
                        "warning": "Su correo electrónico ha sido actualizado. Deberá iniciar sesión con el nuevo correo en su próximo acceso."
                    }
                )
            return current_user

        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        
        
        
    async def login_srv(self, username: str, password: str):
        """This asynchronous function handles user login by authenticating
        with AWS Cognito using a username and password. 
        It initiates the authentication process and returns an access token if successful, 
        or raises an HTTP 401 error for invalid credentials."""

        print(f"Logging in user: {username}")
        
        """Handle direct login with username/password"""
        try:
            auth_response = cognito_client.initiate_auth(
                ClientId=os.getenv('COGNITO_APP_CLIENT_ID'),
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password
                }
            )
            return {
                "access_token": auth_response['AuthenticationResult']['AccessToken'],
                "token_type": "bearer"
            }
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )
            
    
    
    async def login_cognito_srv(self, request):
        """This asynchronous function handles Cognito login by initiating the authorization process.
        It constructs the redirect URI for the authorization request and then calls the Cognito authorization
        endpoint to initiate the login flow. If successful, it returns the authorization response.
        """
        
        """Initiate Cognito login"""
        redirect_uri = request.url_for('auth')
        print(f"Redirect URI: {redirect_uri}")  # Add this line
        return await oauth.cognito.authorize_redirect(request, redirect_uri)
    
    
    
    async def auth_srv(self, request, db: AsyncSession):
        """This asynchronous function handles the Cognito authentication callback. It retrieves the access token, 
        fetches user information, and checks if the user exists in the database by either Cognito sub or email. 
        If the user is found without a Cognito sub, it updates the user's record. If the user does not exist, 
        it raises an HTTP exception. Finally, it redirects the user to the frontend with the access token."""

        """Handle the Cognito callback"""
        try:
            token = await oauth.cognito.authorize_access_token(request)
            
            if 'access_token' in token:
                # Get Cognito user info
                userinfo = await oauth.cognito.userinfo(token=token)
                email = userinfo.get('email')
                sub = userinfo.get('sub')
                
                # Primero intentar encontrar usuario por cognito_sub
                user = db.query(User).filter(User.cognito_sub == sub).first()
                if not user:
                    # Si no se encuentra por cognito_sub, buscar por email
                    user = db.query(User).filter(User.email == email).first()
                    if user and not user.cognito_sub:  # Changed && to and
                        # Si existe el usuario pero no tiene cognito_sub, actualizarlo
                        user.cognito_sub = sub
                        await db.commit()
                    elif not user:
                        # Solo crear nuevo usuario si no existe ni por sub ni por email
                        raise HTTPException(
                            status_code=400, 
                            detail="Usuario no encontrado en el sistema"
                        )
                
                # Redirect to frontend with access token
                frontend_url = "http://localhost:3000"
                response = RedirectResponse(
                    url=f"{frontend_url}?token={token['access_token']}"
                )
                return response
                
            raise HTTPException(status_code=400, detail="Invalid token")
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
        
        
    async def logout_srv(self, request):
        """This asynchronous function handles user logout from Cognito by clearing the session,
        constructing the appropriate logout URL with the required parameters, and returning 
        the logout URL. In case of an error, it logs the error and returns a default logout URL."""
        
        """Handle Cognito logout"""
        try:
            # Clear session
            request.session.clear()
            
            # Construct the correct Cognito domain
            cognito_domain = f"https://us-east-{os.getenv('COGNITO_DOMAIN')}.auth.{os.getenv('AWS_REGION')}.amazoncognito.com"
            
            # Construct logout URL with correct parameters
            logout_url = (
                f"{cognito_domain}/logout?"
                f"client_id={os.getenv('COGNITO_APP_CLIENT_ID')}&"
                f"logout_uri=http://localhost:3000"  # Changed from client_id to actual URL
            )
            
            return {"logoutUrl": logout_url}
            
        except Exception as e:
            print(f"Logout error: {str(e)}")
            return {"logoutUrl": "http://localhost:3000"}