from sqlalchemy import Column, String, DateTime, ForeignKey, Table, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
from db import Base 
import uuid
from datetime import datetime
import enum

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    OPERADOR = "OPERADOR"
    CONDUCTOR = "CONDUCTOR"
    PASAJERO = "PASAJERO"
    TECNICO = "TECNICO"
    JEFE_TALLER = "JEFE_TALLER"
    ADMINISTRATIVO = "ADMINISTRATIVO"

class VehicleStatus(str, enum.Enum):
    ACTIVO = "ACTIVO"
    EN_RUTA = "EN_RUTA"
    MANTENIMIENTO = "MANTENIMIENTO"
    INACTIVO = "INACTIVO"
    BAJA = "BAJA"
    AVERIADO = "AVERIADO"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role = Column(ENUM(UserRole, name='user_role', create_type=False))
    name = Column(String)
    email = Column(String, unique=True)
    identification = Column(String, unique=True)  # Added identification field
    status = Column(String, default="active")
    cognito_sub = Column(String, unique=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id'), nullable=True)
    
    # Relación con la empresa donde trabaja el usuario
    company = relationship("Company", back_populates="users", foreign_keys=[company_id])
    
    # Relación con las empresas que administra
    administered_companies = relationship("Company", back_populates="admin", foreign_keys="Company.admin_id")

class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    nit = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String)
    address = Column(String)
    cognito_group_id = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active")
    admin_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Relación con el administrador de la empresa
    admin = relationship("User", back_populates="administered_companies", foreign_keys=[admin_id])
    
    # Relación con los usuarios que pertenecen a la empresa
    users = relationship("User", back_populates="company", foreign_keys="User.company_id")

    # Relación con los vehículos que pertenecen a la empresa
    vehicles = relationship("Vehicle", back_populates="company")

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand = Column(String, nullable=False)
    model = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    vehicle_type = Column(String, nullable=False)
    plate_number = Column(String, unique=True, nullable=False)
    company_number = Column(String, nullable=False)
    vin = Column(String, unique=True, nullable=True)
    status = Column(ENUM(VehicleStatus, name='vehicle_status', create_type=False), default=VehicleStatus.ACTIVO)
    created_at = Column(DateTime, default=datetime.utcnow)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id'), nullable=False)

    # Relationship with company
    company = relationship("Company", back_populates="vehicles")