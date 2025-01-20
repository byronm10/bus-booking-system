from sqlalchemy import Column, String, DateTime, ForeignKey, Table, Enum, Integer, func, Numeric
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSONB
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
    AYUDANTE = "AYUDANTE"

class VehicleStatus(str, enum.Enum):
    ACTIVO = "ACTIVO"
    EN_RUTA = "EN_RUTA"
    MANTENIMIENTO = "MANTENIMIENTO"
    INACTIVO = "INACTIVO"
    BAJA = "BAJA"
    AVERIADO = "AVERIADO"

class RouteStatus(str, enum.Enum):
    ACTIVA = "ACTIVA"
    EN_EJECUCION = "EN_EJECUCION"
    COMPLETADA = "COMPLETADA"
    SUSPENDIDA = "SUSPENDIDA"

class RepetitionPeriod(str, enum.Enum):
    DIARIO = "DIARIO"
    SEMANAL = "SEMANAL"
    MENSUAL = "MENSUAL"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role = Column(ENUM(UserRole, name='user_role', create_type=False))
    name = Column(String)
    email = Column(String, unique=True)
    identification = Column(String, unique=True, nullable=True)
    license_number = Column(String, unique=True, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
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

    # Relación con las rutas que pertenecen a la empresa
    routes = relationship("Route", back_populates="company")

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

    # Relationship with route executions
    route_executions = relationship("RouteExecution", back_populates="vehicle")

    # Relationship with routes
    routes = relationship("Route", back_populates="vehicle")

class Route(Base):
    __tablename__ = "routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    start_point = Column(String, nullable=False)
    end_point = Column(String, nullable=False)
    intermediate_stops = Column(JSONB, nullable=True, default=[])
    departure_time = Column(DateTime, nullable=False)
    estimated_duration = Column(Integer, nullable=False)  # en minutos
    repetition_frequency = Column(Integer, nullable=True)
    repetition_period = Column(Enum(RepetitionPeriod, name='repetition_period', create_type=False), nullable=True)
    status = Column(Enum(RouteStatus, name='route_status', create_type=False), default=RouteStatus.ACTIVA)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id'), nullable=False)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey('vehicles.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Add this
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # Add this
    base_price = Column(Numeric(10, 2), nullable=False)  # Base price in decimal with 2 decimal places
    stop_prices = Column(JSONB, nullable=True, default=[])  # Prices for intermediate stops
    driver_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    helper_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="routes")
    executions = relationship("RouteExecution", back_populates="route", cascade="all, delete-orphan")
    vehicle = relationship("Vehicle", back_populates="routes")  # Add relationship
    driver = relationship("User", foreign_keys=[driver_id])
    helper = relationship("User", foreign_keys=[helper_id])

class RouteExecution(Base):
    __tablename__ = "route_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(UUID(as_uuid=True), ForeignKey('routes.id'), nullable=False)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey('vehicles.id'), nullable=False)
    
    actual_start_time = Column(DateTime(timezone=True))
    actual_end_time = Column(DateTime(timezone=True))
    actual_duration = Column(Integer)  # Duration in minutes
    incidents = Column(JSONB, nullable=True)  # List of incidents during execution
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(ENUM(RouteStatus, name='route_status', create_type=False), default=RouteStatus.ACTIVA)
    
    # Relationships
    route = relationship("Route", back_populates="executions")
    vehicle = relationship("Vehicle", back_populates="route_executions")