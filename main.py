from fastapi import FastAPI, Depends, HTTPException, status, Form, Request
from sqlalchemy.orm import Session
from db import get_db, Base, engine
from models import User, UserRole
from schemas import UserCreate, UserResponse
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

# Create enum type if it doesn't exist
with engine.connect() as conn:
    try:
        conn.execute(text("CREATE TYPE user_role AS ENUM ('ADMIN', 'OPERATOR', 'DRIVER', 'PASSENGER');"))
        conn.commit()
    except Exception as e:
        conn.rollback()

# Create database tables
Base.metadata.create_all(bind=engine)

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
            
            # Try to find user by email
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                # Create user if they don't exist
                user = User(
                    email=email,
                    name=userinfo.get('name', email),
                    role=UserRole.ADMIN,
                    cognito_sub=sub,  # Set cognito_sub when creating user
                    status='active'
                )
                db.add(user)
                db.commit()
            elif not user.cognito_sub:
                # Update cognito_sub if not set
                user.cognito_sub = sub
                db.commit()
            
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