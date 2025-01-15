from fastapi import FastAPI, Depends, HTTPException, status, Form, Request
from fastapi import Body
from sqlalchemy.orm import Session
from db import get_db, Base, engine
from models import (
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
from schemas import (
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
from typing import List
from uuid import UUID
import hmac
import base64
import hashlib
from fastapi import Query
from sqlalchemy import create_engine, text
from auth import verify_admin, get_current_active_user, cognito_client
from jose import jwt
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2AuthorizationCodeBearer
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
import json
from botocore.exceptions import ClientError
from fastapi.responses import JSONResponse

app = FastAPI()

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=os.urandom(24))

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv('FRONTEND_URL')],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        'redirect_uri': f"{os.getenv('SELF_BACKEND_URL')}/auth"
    }
)

# Initialize database schema
with engine.connect() as conn:
    try:
        # Create enum type if it doesn't exist
        conn.execute(text("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
                    CREATE TYPE user_role AS ENUM (
                        'ADMIN', 
                        'OPERATOR', 
                        'DRIVER', 
                        'PASSENGER', 
                        'TECNICO', 
                        'JEFE_TALLER', 
                        'ADMINISTRATIVO'
                    );
                END IF;
            END $$;
        """))
        conn.commit()
    except Exception as e:
        print(f"Error in database initialization: {str(e)}")
        conn.rollback()

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Re-insert admin user if needed
@app.on_event("startup")
async def startup_event():
    db = next(get_db())
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
            db.commit()
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
        db.rollback()
    finally:
        db.close()

@app.post("/users/", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
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

@app.get("/users/", response_model=List[UserResponse])
def get_users(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    # Get companies administered by current user
    admin_companies = db.query(Company).filter(
        Company.admin_id == current_user.id
    ).all()
    
    # Get company IDs administered by current user
    company_ids = [company.id for company in admin_companies]
    
    # Get users belonging to those companies
    users = db.query(User).filter(User.company_id.in_(company_ids)).all()
    return users

@app.put("/users/profile", response_model=UserResponse)
async def update_profile(
    user_update: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
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
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
async def login(username: str = Form(), password: str = Form()):
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

@app.get("/login")
async def login_cognito(request: Request):
    """Initiate Cognito login"""
    redirect_uri = request.url_for('auth')
    print(f"Redirect URI: {redirect_uri}")  # Add this line
    return await oauth.cognito.authorize_redirect(request, redirect_uri)

@app.get("/auth") 
async def auth(request: Request):
    """Handle the Cognito callback"""
    try:
        token = await oauth.cognito.authorize_access_token(request)
        
        if 'access_token' in token:
            # Get Cognito user info
            userinfo = await oauth.cognito.userinfo(token=token)
            email = userinfo.get('email')
            sub = userinfo.get('sub')
            
            # Get database connection
            db = next(get_db())
            
            # Primero intentar encontrar usuario por cognito_sub
            user = db.query(User).filter(User.cognito_sub == sub).first()
            if not user:
                # Si no se encuentra por cognito_sub, buscar por email
                user = db.query(User).filter(User.email == email).first()
                if user and not user.cognito_sub:  # Changed && to and
                    # Si existe el usuario pero no tiene cognito_sub, actualizarlo
                    user.cognito_sub = sub
                    db.commit()
                elif not user:
                    # Solo crear nuevo usuario si no existe ni por sub ni por email
                    raise HTTPException(
                        status_code=400, 
                        detail="Usuario no encontrado en el sistema"
                    )
            
            response = RedirectResponse(
                url=f"{os.getenv('FRONTEND_URL')}?token={token['access_token']}"
            )
            return response
            
        raise HTTPException(status_code=400, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/logout")
async def logout(request: Request):
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
            f"logout_uri={os.getenv('FRONTEND_URL')}"
        )
        
        return {"logoutUrl": logout_url}
        
    except Exception as e:
        print(f"Logout error: {str(e)}")
        return {"logoutUrl": os.getenv('FRONTEND_URL')}

@app.post("/companies/", response_model=CompanyResponse)
async def create_company(
    company: CompanyCreate,
    db: Session = Depends(get_db),
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

@app.get("/companies/", response_model=List[CompanyResponse])
async def get_companies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
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

@app.get("/companies/{company_id}", response_model=CompanyResponse)
async def get_company_details(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        print(f"Fetching company details - Company ID: {company_id}")
        print(f"Request from user: {current_user.email} (role: {current_user.role})")
        
        # For ADMINISTRATIVO, directly get their company
        if current_user.role == UserRole.ADMINISTRATIVO:
            company = db.query(Company).filter(Company.id == current_user.company_id).first()
            print(f"ADMINISTRATIVO user, fetching their company: {company.id if company else 'Not found'}")
        else:
            # For ADMIN, check company ownership
            company = db.query(Company).filter(
                Company.id == company_id,
                Company.admin_id == current_user.id
            ).first()
            print(f"ADMIN user, fetching owned company: {company.id if company else 'Not found'}")
        
        if not company:
            print(f"Company not found or access denied for ID: {company_id}")
            raise HTTPException(
                status_code=404, 
                detail="Empresa no encontrada o no tiene permisos para verla"
            )
            
        print(f"Company found: {company.name}")
        return company
        
    except Exception as e:
        print(f"Error in get_company_details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener detalles de la empresa: {str(e)}"
        )

@app.put("/companies/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: UUID,
    company_update: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        # Get existing company
        db_company = db.query(Company).filter(Company.id == company_id).first()
        if not db_company:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
            
        # Check if user has access to this company
        if current_user.email != "admin@busfleet.com" and db_company.admin_id != current_user.id:
            raise HTTPException(
                status_code=403, 
                detail="No tiene permisos para modificar esta empresa"
            )

        # Update Cognito group name if name changed
        if db_company.name != company_update.name:
            new_group_name = company_update.name.lower().replace(" ", "_")
            try:
                # Update group in Cognito
                cognito_client.update_group(
                    GroupName=db_company.cognito_group_id,
                    UserPoolId=os.getenv('COGNITO_USER_POOL_ID'),
                    Description=f"Grupo para la empresa de transporte: {company_update.name}"
                )
                db_company.cognito_group_id = new_group_name
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error actualizando grupo en Cognito: {str(e)}")

        # Update company fields
        for key, value in company_update.model_dump().items():
            setattr(db_company, key, value)

        db.commit()
        db.refresh(db_company)
        return db_company

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/companies/{company_id}")
async def delete_company(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        # Get company
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
            
        # Check if user has access to this company
        if current_user.email != "admin@busfleet.com" and company.admin_id != current_user.id:
            raise HTTPException(
                status_code=403, 
                detail="No tiene permisos para eliminar esta empresa"
            )

        # Delete Cognito group
        try:
            cognito_client.delete_group(
                GroupName=company.cognito_group_id,
                UserPoolId=os.getenv('COGNITO_USER_POOL_ID')
            )
        except Exception as e:
            print(f"Error deleting Cognito group: {str(e)}")

        # Delete company from database
        db.delete(company)
        db.commit()
        return {"message": "Empresa eliminada exitosamente"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's profile"""
    return current_user

@app.get("/users/by-company/{company_id}", response_model=List[UserResponse])
async def get_users_by_company(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get users for a specific company"""
    # Verify company belongs to admin
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.admin_id == current_user.id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para ver usuarios de esta empresa"
        )

    users = db.query(User).filter(User.company_id == company_id).all()
    return users

@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_update: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        print(f"Updating user request from user: {current_user.email} (role: {current_user.role})")
        print(f"User ID: {user_id}")
        print(f"Update data: {user_update.model_dump()}")

        # Get existing user
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Check permissions and verify company access based on role
        if current_user.role == UserRole.ADMIN:
            # Admin must own the company
            company = db.query(Company).filter(
                Company.id == db_user.company_id,
                Company.admin_id == current_user.id
            ).first()
        else:
            # ADMINISTRATIVO must belong to the same company
            if current_user.role != UserRole.ADMINISTRATIVO:
                raise HTTPException(
                    status_code=403,
                    detail="No tiene permisos para modificar usuarios"
                )
            
            # Check if user belongs to same company as ADMINISTRATIVO
            company = db.query(Company).filter(
                Company.id == db_user.company_id,
                Company.id == current_user.company_id
            ).first()

            # ADMINISTRATIVO can't modify ADMIN or other ADMINISTRATIVO users
            if db_user.role in [UserRole.ADMIN, UserRole.ADMINISTRATIVO]:
                raise HTTPException(
                    status_code=403,
                    detail="No tiene permisos para modificar usuarios administrativos o administradores"
                )

            # ADMINISTRATIVO can't change role to ADMIN or ADMINISTRATIVO
            if user_update.role in [UserRole.ADMIN, UserRole.ADMINISTRATIVO]:
                raise HTTPException(
                    status_code=403,
                    detail="No puede asignar roles administrativos o de administrador"
                )

        if not company:
            raise HTTPException(
                status_code=403,
                detail="No tiene permisos para modificar este usuario"
            )

        # Update Cognito user attributes
        try:
            cognito_client.admin_update_user_attributes(
                UserPoolId=os.getenv('COGNITO_USER_POOL_ID'),
                Username=db_user.email,
                UserAttributes=[
                    {'Name': 'email', 'Value': user_update.email},
                    {'Name': 'email_verified', 'Value': 'true'},
                    {'Name': 'name', 'Value': user_update.name},
                    {'Name': 'custom:role', 'Value': user_update.role}
                ]
            )
        except Exception as e:
            print(f"Error updating Cognito user: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error updating Cognito user: {str(e)}"
            )

        # Update database user
        for key, value in user_update.model_dump().items():
            setattr(db_user, key, value)

        db.commit()
        db.refresh(db_user)
        return db_user

    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        print(f"Error updating user: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar el usuario: {str(e)}"
        )

@app.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        # Get user to delete
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Verify admin has access to this user's company
        company = db.query(Company).filter(
            Company.id == db_user.company_id,
            Company.admin_id == current_user.id
        ).first()
        
        if not company:
            raise HTTPException(
                status_code=403,
                detail="No tiene permisos para eliminar este usuario"
            )

        # Delete user from Cognito
        try:
            cognito_client.admin_delete_user(
                UserPoolId=os.getenv('COGNITO_USER_POOL_ID'),
                Username=db_user.email
            )
        except Exception as e:
            print(f"Error deleting user from Cognito: {str(e)}")
            # Continue with database deletion even if Cognito fails
            # The user might not exist in Cognito

        # Delete user from database
        db.delete(db_user)
        db.commit()
        
        return {"message": "Usuario eliminado exitosamente"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error deleting user: {str(e)}"
        )

@app.post("/vehicles/", response_model=VehicleResponse)
async def create_vehicle(
    vehicle: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        print(f"Creating vehicle request received from user: {current_user.email} (role: {current_user.role})")
        print(f"Vehicle data: {vehicle.model_dump()}")

        # Convert empty string VIN to None
        if not vehicle.vin:
            vehicle.vin = None

        # Check if user has permission (ADMIN or ADMINISTRATIVO)
        if current_user.role not in [UserRole.ADMIN, UserRole.ADMINISTRATIVO]:
            print(f"Permission denied: User {current_user.email} with role {current_user.role} attempted to create vehicle")
            raise HTTPException(
                status_code=403,
                detail="Solo administradores y administrativos pueden crear vehículos"
            )

        # Get company and verify access based on role
        if current_user.role == UserRole.ADMIN:
            # Admin must own the company
            company = db.query(Company).filter(
                Company.id == vehicle.company_id,
                Company.admin_id == current_user.id
            ).first()
        else:
            # ADMINISTRATIVO must belong to the company
            company = db.query(Company).filter(
                Company.id == vehicle.company_id,
                Company.id == current_user.company_id
            ).first()

        print(f"Checking company access - Company ID: {vehicle.company_id}")
        if not company:
            print(f"Company access denied for user {current_user.email}")
            raise HTTPException(
                status_code=403,
                detail="No tiene permisos para añadir vehículos a esta empresa"
            )

        print(f"Company verification successful: {company.name}")

        # Check for duplicate plate number
        existing_vehicle = db.query(Vehicle).filter(
            Vehicle.plate_number == vehicle.plate_number
        ).first()
        if existing_vehicle:
            print(f"Duplicate plate number found: {vehicle.plate_number}")
            raise HTTPException(
                status_code=400,
                detail="Ya existe un vehículo con este número de placa"
            )

        # Check for duplicate company number within the same company
        existing_company_number = db.query(Vehicle).filter(
            Vehicle.company_number == vehicle.company_number,
            Vehicle.company_id == vehicle.company_id
        ).first()
        if existing_company_number:
            print(f"Duplicate company number found: {vehicle.company_number} in company {company.name}")
            raise HTTPException(
                status_code=400,
                detail="Ya existe un vehículo con este número en la empresa"
            )

        # Create vehicle
        try:
            print("Attempting to create vehicle in database")
            db_vehicle = Vehicle(**vehicle.model_dump())
            db.add(db_vehicle)
            db.commit()
            db.refresh(db_vehicle)
            print(f"Vehicle created successfully: ID {db_vehicle.id}")
            return db_vehicle
        except Exception as db_error:
            print(f"Database error while creating vehicle: {str(db_error)}")
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error al crear el vehículo en la base de datos: {str(db_error)}"
            )

    except HTTPException as http_error:
        # Re-raise HTTP exceptions with their original status codes
        raise http_error
    except Exception as e:
        print(f"Unexpected error in create_vehicle: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error inesperado al crear el vehículo: {str(e)}"
        )

@app.get("/vehicles/", response_model=List[VehicleResponse])
async def get_vehicles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        # Get companies administered by current user
        admin_companies = db.query(Company).filter(
            Company.admin_id == current_user.id
        ).all()
        
        company_ids = [company.id for company in admin_companies]
        
        # Get vehicles for those companies
        vehicles = db.query(Vehicle).filter(
            Vehicle.company_id.in_(company_ids)
        ).all()
        
        return vehicles
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching vehicles: {str(e)}"
        )

@app.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    vehicle = db.query(Vehicle).filter(
        Vehicle.id == vehicle_id,
        Vehicle.company_id.in_(
            db.query(Company.id).filter(Company.admin_id == current_user.id)
        )
    ).first()
    
    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail="Vehículo no encontrado o no tiene permisos para verlo"
        )
    
    return vehicle

@app.put("/vehicles/{vehicle_id}/status", response_model=VehicleResponse)
async def update_vehicle_status(
    vehicle_id: UUID,
    data: dict,  # Change to accept dict instead of direct VehicleStatus
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        print(f"Updating vehicle status - Vehicle ID: {vehicle_id}")
        print(f"Request data: {data}")
        print(f"Request from user: {current_user.email} (role: {current_user.role})")

        # Convert string status to enum
        try:
            new_status = VehicleStatus(data.get('status'))
        except ValueError as e:
            print(f"Invalid status value: {data.get('status')}")
            raise HTTPException(
                status_code=400,
                detail=f"Estado de vehículo inválido. Valores permitidos: {[status.value for status in VehicleStatus]}"
            )

        # Check permissions
        if current_user.role not in [UserRole.ADMIN, UserRole.ADMINISTRATIVO, UserRole.JEFE_TALLER]:
            print(f"Permission denied for user {current_user.email}")
            raise HTTPException(
                status_code=403,
                detail="No tiene permisos para actualizar el estado del vehículo"
            )

        # Get vehicle and verify ownership based on role
        if current_user.role == UserRole.ADMIN:
            vehicle = db.query(Vehicle).filter(
                Vehicle.id == vehicle_id,
                Vehicle.company_id.in_(
                    db.query(Company.id).filter(Company.admin_id == current_user.id)
                )
            ).first()
        else:
            vehicle = db.query(Vehicle).filter(
                Vehicle.id == vehicle_id,
                Vehicle.company_id == current_user.company_id
            ).first()

        if not vehicle:
            print(f"Vehicle {vehicle_id} not found or access denied")
            raise HTTPException(
                status_code=404,
                detail="Vehículo no encontrado o no tiene permisos para modificarlo"
            )

        print(f"Current vehicle status: {vehicle.status}")
        print(f"Updating to new status: {new_status}")

        # Update status
        vehicle.status = new_status
        db.commit()
        db.refresh(vehicle)
        
        print(f"Vehicle status updated successfully")
        return vehicle

    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        print(f"Error updating vehicle status: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar el estado del vehículo: {str(e)}"
        )
@app.put("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: UUID,
    vehicle_update: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        print(f"Updating vehicle - Vehicle ID: {vehicle_id}")
        print(f"Update data: {vehicle_update.model_dump()}")
        print(f"Request from user: {current_user.email} (role: {current_user.role})")

        # Convert empty string VIN to None
        if not vehicle_update.vin:
            vehicle_update.vin = None

        # Check permissions
        if current_user.role not in [UserRole.ADMIN, UserRole.ADMINISTRATIVO]:
            print(f"Permission denied for user {current_user.email}")
            raise HTTPException(
                status_code=403,
                detail="Solo administradores y administrativos pueden modificar vehículos"
            )

        # Get vehicle and verify ownership based on role
        if current_user.role == UserRole.ADMIN:
            vehicle = db.query(Vehicle).filter(
                Vehicle.id == vehicle_id,
                Vehicle.company_id.in_(
                    db.query(Company.id).filter(Company.admin_id == current_user.id)
                )
            ).first()
        else:
            vehicle = db.query(Vehicle).filter(
                Vehicle.id == vehicle_id,
                Vehicle.company_id == current_user.company_id
            ).first()

        if not vehicle:
            print(f"Vehicle {vehicle_id} not found or access denied")
            raise HTTPException(
                status_code=404,
                detail="Vehículo no encontrado o no tiene permisos para modificarlo"
            )

        # Check for duplicate plate number if changed
        if vehicle_update.plate_number != vehicle.plate_number:
            existing_vehicle = db.query(Vehicle).filter(
                Vehicle.plate_number == vehicle_update.plate_number,
                Vehicle.id != vehicle_id
            ).first()
            if existing_vehicle:
                raise HTTPException(
                    status_code=400,
                    detail="Ya existe un vehículo con este número de placa"
                )

        # Check for duplicate company number if changed
        if vehicle_update.company_number != vehicle.company_number:
            existing_company_number = db.query(Vehicle).filter(
                Vehicle.company_number == vehicle_update.company_number,
                Vehicle.company_id == vehicle_update.company_id,
                Vehicle.id != vehicle_id
            ).first()
            if existing_company_number:
                raise HTTPException(
                    status_code=400,
                    detail="Ya existe un vehículo con este número en la empresa"
                )

        # Check for duplicate VIN if changed and not None
        if vehicle_update.vin and vehicle_update.vin != vehicle.vin:
            existing_vin = db.query(Vehicle).filter(
                Vehicle.vin == vehicle_update.vin,
                Vehicle.id != vehicle_id
            ).first()
            if existing_vin:
                raise HTTPException(
                    status_code=400,
                    detail="Ya existe un vehículo con este VIN"
                )

        # Update vehicle fields
        for key, value in vehicle_update.model_dump().items():
            setattr(vehicle, key, value)

        db.commit()
        db.refresh(vehicle)
        print(f"Vehicle updated successfully")
        return vehicle

    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        print(f"Error updating vehicle: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar el vehículo: {str(e)}"
        )

@app.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        print(f"Deleting vehicle - Vehicle ID: {vehicle_id}")
        print(f"Request from user: {current_user.email} (role: {current_user.role})")

        # Check permissions
        if current_user.role not in [UserRole.ADMIN, UserRole.ADMINISTRATIVO]:
            raise HTTPException(
                status_code=403,
                detail="Solo administradores y administrativos pueden eliminar vehículos"
            )

        # Get vehicle and verify ownership
        vehicle = db.query(Vehicle).filter(
            Vehicle.id == vehicle_id,
            Vehicle.company_id.in_(
                db.query(Company.id).filter(Company.admin_id == current_user.id)
            )
        ).first()

        if not vehicle:
            raise HTTPException(
                status_code=404,
                detail="Vehículo no encontrado o no tiene permisos para eliminarlo"
            )

        # Delete vehicle
        db.delete(vehicle)
        db.commit()
        print(f"Vehicle deleted successfully")
        return {"message": "Vehículo eliminado exitosamente"}

    except Exception as e:
        print(f"Error deleting vehicle: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar el vehículo: {str(e)}"
        )

@app.post("/routes/", response_model=RouteResponse)
async def create_route(
    route: RouteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        print(f"Creating route request from user: {current_user.email} (role: {current_user.role})")
        print(f"Route data: {route.model_dump()}")

        # Check permissions and verify company access - keep this part

        # Create route
        route_data = route.model_dump()
        
        # Convert intermediate stops to JSON format
        if route.intermediate_stops:
            route_data['intermediate_stops'] = [stop.model_dump() for stop in route.intermediate_stops]
        
        db_route = Route(**route_data)
        db.add(db_route)
        db.commit()
        db.refresh(db_route)

        return db_route

    except Exception as e:
        print(f"Error creating route: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear la ruta: {str(e)}"
        )

@app.get("/routes/", response_model=List[RouteResponse])
async def get_routes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        # Get companies administered by current user
        companies = db.query(Company).filter(
            Company.admin_id == current_user.id
        ).all()
        
        company_ids = [company.id for company in companies]
        
        # Get routes for those companies
        routes = db.query(Route).filter(
            Route.company_id.in_(company_ids)
        ).all()
        
        return routes

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener las rutas: {str(e)}"
        )

@app.get("/routes/{route_id}", response_model=RouteResponse)
async def get_route(
    route_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        route = db.query(Route).filter(
            Route.id == route_id,
            Route.company_id.in_(
                db.query(Company.id).filter(Company.admin_id == current_user.id)
            )
        ).first()

        if not route:
            raise HTTPException(
                status_code=404,
                detail="Ruta no encontrada o no tiene permisos para verla"
            )

        return route

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener la ruta: {str(e)}"
        )
@app.put("/routes/{route_id}", response_model=RouteResponse)
async def update_route(
    route_id: UUID,
    route_update: RouteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        print(f"Updating route request from user: {current_user.email} (role: {current_user.role})")
        print(f"Route ID: {route_id}")
        print(f"Update data: {route_update.model_dump()}")

        # Check permissions
        if current_user.role not in [UserRole.ADMIN, UserRole.ADMINISTRATIVO]:
            print(f"Permission denied for user {current_user.email}")
            raise HTTPException(
                status_code=403,
                detail="Solo administradores y administrativos pueden modificar rutas"
            )

        # Get route and verify ownership based on role
        if current_user.role == UserRole.ADMIN:
            # Admin must own the company
            route = db.query(Route).filter(
                Route.id == route_id,
                Route.company_id.in_(
                    db.query(Company.id).filter(Company.admin_id == current_user.id)
                )
            ).first()
        else:
            # ADMINISTRATIVO must belong to that company
            route = db.query(Route).filter(
                Route.id == route_id,
                Route.company_id == current_user.company_id
            ).first()

        if not route:
            print(f"Route {route_id} not found or access denied")
            raise HTTPException(
                status_code=404,
                detail="Ruta no encontrada o no tiene permisos para modificarla"
            )

        # Check if route can be updated
        if route.status not in [RouteStatus.ACTIVA, RouteStatus.SUSPENDIDA]:
            raise HTTPException(
                status_code=400,
                detail="Solo se pueden modificar rutas activas o suspendidas"
            )

        # Validate intermediate stops
        if route_update.intermediate_stops:
            total_stop_time = sum(stop.estimated_stop_time for stop in route_update.intermediate_stops)
            if total_stop_time >= route_update.estimated_duration:
                raise HTTPException(
                    status_code=400,
                    detail="El tiempo total de paradas no puede ser mayor o igual a la duración estimada de la ruta"
                )

        # Prepare update data with intermediate stops conversion
        update_data = route_update.model_dump()
        if route_update.intermediate_stops:
            update_data['intermediate_stops'] = [stop.model_dump() for stop in route_update.intermediate_stops]

        # Update route fields
        for key, value in update_data.items():
            setattr(route, key, value)

        db.commit()
        db.refresh(route)
        return route

    except Exception as e:
        print(f"Error updating route: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar la ruta: {str(e)}"
        )
@app.put("/routes/{route_id}/status", response_model=RouteResponse)
async def update_route_status(
    route_id: UUID,
    status: RouteStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        # Check permissions
        if current_user.role not in [UserRole.ADMIN, UserRole.ADMINISTRATIVO, UserRole.OPERADOR]:
            raise HTTPException(
                status_code=403,
                detail="No tiene permisos para cambiar el estado de las rutas"
            )

        # Get route and verify ownership
        route = db.query(Route).filter(
            Route.id == route_id,
            Route.company_id.in_(
                db.query(Company.id).filter(Company.admin_id == current_user.id)
            )
        ).first()

        if not route:
            raise HTTPException(
                status_code=404,
                detail="Ruta no encontrada o no tiene permisos para modificarla"
            )

        # Update status
        route.status = status
        db.commit()
        db.refresh(route)
        return route

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar el estado de la ruta: {str(e)}"
        )

@app.delete("/routes/{route_id}")
async def delete_route(
    route_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        # Check permissions
        if current_user.role not in [UserRole.ADMIN, UserRole.ADMINISTRATIVO]:
            raise HTTPException(
                status_code=403,
                detail="Solo administradores y administrativos pueden eliminar rutas"
            )

        # Get route and verify ownership
        route = db.query(Route).filter(
            Route.id == route_id,
            Route.company_id.in_(
                db.query(Company.id).filter(Company.admin_id == current_user.id)
            )
        ).first()

        if not route:
            raise HTTPException(
                status_code=404,
                detail="Ruta no encontrada o no tiene permisos para eliminarla"
            )

        # Check if route can be deleted
        if route.status not in [RouteStatus.ACTIVA, RouteStatus.SUSPENDIDA]:
            raise HTTPException(
                status_code=400,
                detail="Solo se pueden eliminar rutas activas o suspendidas"
            )

        # Delete route
        db.delete(route)
        db.commit()
        return {"message": "Ruta eliminada exitosamente"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar la ruta: {str(e)}"
        )

@app.get("/users/company/{company_id}")
async def get_company_users(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get users for a specific company"""
    if current_user.role not in [UserRole.ADMIN, UserRole.ADMINISTRATIVO]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Verify user belongs to company
    if current_user.role == UserRole.ADMINISTRATIVO and current_user.company_id != company_id:
        raise HTTPException(status_code=403, detail="Not authorized for this company")
    
    users = db.query(User).filter(User.company_id == company_id).all()
    return users

@app.get("/vehicles/company/{company_id}")
async def get_company_vehicles(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get vehicles for a specific company"""
    if current_user.role not in [UserRole.ADMIN, UserRole.ADMINISTRATIVO]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if current_user.role == UserRole.ADMINISTRATIVO and current_user.company_id != company_id:
        raise HTTPException(status_code=403, detail="Not authorized for this company")
    
    vehicles = db.query(Vehicle).filter(Vehicle.company_id == company_id).all()
    return vehicles

@app.get("/routes/company/{company_id}")
async def get_company_routes(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get routes for a specific company"""
    if current_user.role not in [UserRole.ADMIN, UserRole.ADMINISTRATIVO]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if current_user.role == UserRole.ADMINISTRATIVO and current_user.company_id != company_id:
        raise HTTPException(status_code=403, detail="Not authorized for this company")
    
    routes = db.query(Route).filter(Route.company_id == company_id).all()
    return routes

def get_secret_hash(username: str) -> str:
    """Calculate the secret hash for Cognito operations"""
    message = username + os.getenv('COGNITO_APP_CLIENT_ID')
    dig = hmac.new(
        str(os.getenv('COGNITO_APP_CLIENT_SECRET')).encode('utf-8'),
        msg=message.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()

@app.post("/forgot-password")
async def forgot_password(
    email: str = Query(..., description="Email address for password reset"),
    db: Session = Depends(get_db)
):
    try:
        # First verify user exists in our database
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        # Calculate secret hash
        secret_hash = get_secret_hash(email)

        # Only use forgot_password since we want email delivery
        cognito_client.forgot_password(
            ClientId=os.getenv('COGNITO_APP_CLIENT_ID'),
            Username=email,
            SecretHash=secret_hash
        )
        
        return {"message": "Se ha enviado un código de recuperación a su correo electrónico"}
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        if error_code == 'UserNotFoundException':
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        elif error_code == 'LimitExceededException':
            raise HTTPException(
                status_code=429,
                detail="Demasiados intentos. Por favor espere unos minutos"
            )
        else:
            print(f"Cognito error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Error al procesar la solicitud"
            )

@app.post("/reset-password")
async def reset_password(
    email: str = Body(..., description="User email"),
    code: str = Body(..., description="Verification code"),
    new_password: str = Body(..., description="New password"),
    db: Session = Depends(get_db)
):
    try:
        # Verify user exists in our database
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        # Calculate secret hash
        secret_hash = get_secret_hash(email)

        # Confirm password reset in Cognito
        cognito_client.confirm_forgot_password(
            ClientId=os.getenv('COGNITO_APP_CLIENT_ID'),
            Username=email,
            ConfirmationCode=code,
            Password=new_password,
            SecretHash=secret_hash
        )
        
        return {"message": "Contraseña actualizada exitosamente"}
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'CodeMismatchException':
            raise HTTPException(
                status_code=400,
                detail="Código de verificación inválido"
            )
        elif error_code == 'ExpiredCodeException':
            raise HTTPException(
                status_code=400,
                detail="El código ha expirado. Por favor solicite uno nuevo"
            )
        elif error_code == 'InvalidPasswordException':
            raise HTTPException(
                status_code=400,
                detail="La contraseña no cumple con los requisitos de seguridad"
            )
        else:
            print(f"Cognito error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Error al procesar la solicitud"
            )