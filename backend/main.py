from fastapi import FastAPI, Depends, HTTPException, status, Form, Request
from sqlalchemy.orm import Session
from db import get_db, Base, engine
from models import User, UserRole, Company  # Quitamos CompanyResponse de aquí
from schemas import UserCreate, UserResponse, CompanyCreate, CompanyResponse  # Agregamos CompanyCreate y CompanyResponse aquí
from typing import List
from uuid import UUID
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

app = FastAPI()

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=os.urandom(24))

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
        'redirect_uri': 'http://localhost:8000/auth'
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
                    CREATE TYPE user_role AS ENUM ('ADMIN', 'OPERATOR', 'DRIVER', 'PASSENGER');
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
def create_user(user: UserCreate, db: Session = Depends(get_db), admin: User = Depends(verify_admin)):
    user_dict = user.model_dump()
    db_user = User(**user_dict)
    
    try:
        # Create user in Cognito
        cognito_response = cognito_client.admin_create_user(
            UserPoolId=os.getenv('COGNITO_USER_POOL_ID'),
            Username=user.email,
            UserAttributes=[
                {'Name': 'email', 'Value': user.email},
                {'Name': 'name', 'Value': user.name},
                {'Name': 'custom:role', 'Value': user.role.value}  # Store role in Cognito
            ],
            TemporaryPassword='Temp123!'  # User will be forced to change this
        )
        
        # Save Cognito sub in database
        db_user.cognito_sub = cognito_response['User']['Username']
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    users = db.query(User).all()
    return users

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
                if user and not user.cognito_sub:
                    # Si existe el usuario pero no tiene cognito_sub, actualizarlo
                    user.cognito_sub = sub
                    db.commit()
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
            f"logout_uri=http://localhost:3000"  # Changed from client_id to actual URL
        )
        
        return {"logoutUrl": logout_url}
        
    except Exception as e:
        print(f"Logout error: {str(e)}")
        return {"logoutUrl": "http://localhost:3000"}

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
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.admin_id == current_user.id  # Solo acceso a sus propias empresas
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=404, 
            detail="Empresa no encontrada o no tiene permisos para verla"
        )
        
    return company

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