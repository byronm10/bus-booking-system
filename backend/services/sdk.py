from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# BBARRIOS------------------------------------------------------
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi import Depends
# BBARRIOS------------------------------------------------------

load_dotenv()

DB_USER = os.getenv("DATABASE_USER")
DB_PASSWORD = os.getenv("DATABASE_PASSWORD")
DB_HOST = os.getenv("DATABASE_HOST")
DB_NAME = os.getenv("DATABASE_NAME")
SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
     
     
     
     
# BBARRIOS------------------------------------------------------

DATABASE_URL = "postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# Create an asynchronous engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create a configured "Session" class
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
   
# Dependency to get the database session
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session  # This will return the session to the caller
        # The session will be closed automatically after this point
        
# BBARRIOS------------------------------------------------------

