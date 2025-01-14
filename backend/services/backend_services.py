from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from passlib.context import CryptContext

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


class backend_services():    
        
    async def create_admin_user(self, db: AsyncSession):
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