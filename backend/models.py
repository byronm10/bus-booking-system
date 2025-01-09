from sqlalchemy import Column, String, DateTime, ForeignKey, Table, Enum
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
from db import Base 
import uuid
from datetime import datetime
import enum

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    DRIVER = "DRIVER"
    PASSENGER = "PASSENGER"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role = Column(ENUM(UserRole, name='user_role', create_type=False))
    name = Column(String)
    email = Column(String, unique=True)
    status = Column(String, default="active")
    cognito_sub = Column(String, unique=True)