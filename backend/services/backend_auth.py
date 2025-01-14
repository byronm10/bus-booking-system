from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import boto3
import os
import requests


from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.sdk import get_db, Base, engine
from api.schemas.backend_models import User, UserRole

cognito_client = boto3.client('cognito-idp',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

COGNITO_REGION = os.getenv('AWS_REGION')
COGNITO_USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
COGNITO_JWKS_URL = f'https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json'

# Cache the JWKS
jwks = requests.get(COGNITO_JWKS_URL).json()

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"https://{os.getenv('COGNITO_DOMAIN')}.auth.{COGNITO_REGION}.amazoncognito.com/oauth2/authorize",
    tokenUrl=f"https://{os.getenv('COGNITO_DOMAIN')}.auth.{COGNITO_REGION}.amazoncognito.com/oauth2/token"
)

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode token without verification first to get the key ID
        unverified_headers = jwt.get_unverified_headers(token)
        kid = unverified_headers['kid']
        
        # Find the right key from JWKS
        key = None
        for jwk in jwks['keys']:
            if jwk['kid'] == kid:
                key = jwk
                break
        
        if not key:
            raise credentials_exception

        # Verify and decode the token
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=os.getenv('COGNITO_APP_CLIENT_ID')
        )
        
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
            
        # Try to find user by cognito_sub
        user = db.query(User).filter(User.cognito_sub == username).first()
        if user is None:
            # If user exists by email but has no cognito_sub, update it
            email = payload.get("email")
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.cognito_sub = username
                db.commit()
            else:
                raise credentials_exception
            
        return user
    except JWTError:
        raise credentials_exception

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.status != "active":
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def verify_admin(user: User = Depends(get_current_active_user)):
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return user