"""
Internal models for the Service Integration service.

These models are used for database operations with SQLAlchemy.
"""
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, 
    Boolean, JSON, ForeignKey, Table, Text
)
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from shared.utils.src.database import UUID, generate_uuid
from shared.models.src.base import StandardModel, enum_column
from shared.models.src.enums import (
    ServiceStatus, ServiceType, WorkflowStatus, WorkflowType
)

# Define a custom enum for CircuitBreakerState since it's not in shared enums
class CircuitBreakerState(str, Enum):
    """States of a circuit breaker."""
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class RegisteredService(StandardModel):
    """Model for storing registered services."""
    __tablename__ = "registered_service"

    service_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    type = enum_column(ServiceType, nullable=False)
    version = Column(String, nullable=False)
    base_url = Column(String, nullable=False)
    health_check_url = Column(String, nullable=False)
    status = enum_column(ServiceStatus, nullable=False, default=ServiceStatus.ONLINE)
    last_heartbeat = Column(DateTime, nullable=False, default=datetime.now)
    registered_at = Column(DateTime, nullable=False, default=datetime.now)
    endpoints = Column(JSON, nullable=True)
    service_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' which is reserved in SQLAlchemy

    # Enum validation
    __enum_columns__ = {
        'type': ServiceType,
        'status': ServiceStatus
    }

    # Relationships
    circuit_breaker = relationship("CircuitBreakerState", back_populates="service", uselist=False)
    workflow_executions = relationship("WorkflowExecution", back_populates="service")


class CircuitBreakerState(StandardModel):
    """Model for storing circuit breaker states."""
    __tablename__ = "circuit_breaker_state"

    service_id = Column(String, ForeignKey("registered_service.service_id"), unique=True, nullable=False)
    state = enum_column(CircuitBreakerState, nullable=False, default=CircuitBreakerState.CLOSED)
    failure_count = Column(Integer, nullable=False, default=0)
    last_failure_time = Column(DateTime, nullable=True)
    half_open_call_count = Column(Integer, nullable=False, default=0)

    # Enum validation
    __enum_columns__ = {
        'state': CircuitBreakerState
    }

    # Relationships
    service = relationship("RegisteredService", back_populates="circuit_breaker")


class WorkflowExecution(StandardModel):
    """Model for storing workflow executions."""
    __tablename__ = "workflow_execution"

    workflow_id = Column(String, unique=True, nullable=False)
    workflow_type = enum_column(WorkflowType, nullable=False)
    service_id = Column(String, ForeignKey("registered_service.service_id"), nullable=True)
    status = enum_column(WorkflowStatus, nullable=False, default=WorkflowStatus.PENDING)
    data = Column(JSON, nullable=False)
    options = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    errors = Column(JSON, nullable=True)
    start_time = Column(DateTime, nullable=False, default=datetime.now)
    end_time = Column(DateTime, nullable=True)
    execution_time = Column(Float, nullable=True)

    # Enum validation
    __enum_columns__ = {
        'workflow_type': WorkflowType,
        'status': WorkflowStatus
    }

    # Relationships
    service = relationship("RegisteredService", back_populates="workflow_executions")
    workflow_steps = relationship("WorkflowStep", back_populates="workflow_execution")


class WorkflowStep(StandardModel):
    """Model for storing workflow execution steps."""
    __tablename__ = "workflow_step"

    workflow_id = Column(String, ForeignKey("workflow_execution.workflow_id"), nullable=False)
    step_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = enum_column(WorkflowStatus, nullable=False, default=WorkflowStatus.PENDING)
    start_time = Column(DateTime, nullable=False, default=datetime.now)
    end_time = Column(DateTime, nullable=True)
    execution_time = Column(Float, nullable=True)
    result = Column(JSON, nullable=True)
    errors = Column(JSON, nullable=True)

    # Enum validation
    __enum_columns__ = {
        'status': WorkflowStatus
    }

    # Relationships
    workflow_execution = relationship("WorkflowExecution", back_populates="workflow_steps")


class ServiceIntegrationConfig(StandardModel):
    """Model for storing service integration configuration."""
    __tablename__ = "service_integration_config"

    key = Column(String, unique=True, nullable=False)
    value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
