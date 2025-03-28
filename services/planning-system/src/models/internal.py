"""
Planning System Service internal SQLAlchemy models.

This module defines SQLAlchemy ORM models for database entities
used by the Planning System service.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, ForeignKey, Integer, Float, DateTime, Boolean, JSON, Text, Table
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, Mapped, mapped_column

# Import shared components
from shared.models.src.base import StandardModel, enum_column, Base
from shared.utils.src.database import UUID, generate_uuid

# Import shared enums
from shared.models.src.enums import TaskStatus, DependencyType, ResourceType, TaskPriority
from shared.models.src.enums import ProjectStatus, OptimizationTarget

# Use ProjectStatus values for now, but this should be replaced with a proper PlanStatus enum
PlanStatus = ProjectStatus

# Association tables
task_dependencies = Table(
    "task_dependency",
    StandardModel.metadata,
    Column("from_task_id", UUID, ForeignKey("planning_task.id"), primary_key=True),
    Column("to_task_id", UUID, ForeignKey("planning_task.id"), primary_key=True),
    Column("dependency_type", String(20), default=DependencyType.FINISH_TO_START.value),
    Column("lag", Float, default=0),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
)

# Entity tables
class StrategicPlanModel(StandardModel):
    """Strategic plan database model"""
    __tablename__ = "strategic_plan"
    
    project_id = Column(UUID, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    constraints = Column(JSON, nullable=True)
    objectives = Column(JSON, nullable=False)
    status = enum_column(PlanStatus, default=PlanStatus.DRAFT)
    methodology_id = Column(UUID, ForeignKey("planning_methodology.id"), nullable=True)
    template_id = Column(UUID, ForeignKey("plan_template.id"), nullable=True)
    
    # Define enum columns for validation
    __enum_columns__ = {
        'status': PlanStatus
    }
    
    # Relationships
    phases = relationship("PlanPhaseModel", back_populates="plan", cascade="all, delete-orphan")
    milestones = relationship("PlanMilestoneModel", back_populates="plan", cascade="all, delete-orphan")
    tasks = relationship("PlanningTaskModel", back_populates="plan", cascade="all, delete-orphan")
    methodology = relationship("PlanningMethodologyModel", back_populates="plans")
    template = relationship("PlanTemplateModel", back_populates="plans")
    
    def __repr__(self):
        return f"<StrategicPlanModel(id='{self.id}', name='{self.name}', status='{self.status}')>"


class PlanPhaseModel(StandardModel):
    """Plan phase database model"""
    __tablename__ = "plan_phase"
    
    plan_id = Column(UUID, ForeignKey("strategic_plan.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, nullable=False, default=0)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    objectives = Column(JSON, nullable=True)
    deliverables = Column(JSON, nullable=True)
    completion_criteria = Column(JSON, nullable=True)
    
    # Relationships
    plan = relationship("StrategicPlanModel", back_populates="phases")
    tasks = relationship("PlanningTaskModel", back_populates="phase")
    
    def __repr__(self):
        return f"<PlanPhaseModel(id='{self.id}', name='{self.name}', plan_id='{self.plan_id}')>"


class PlanMilestoneModel(StandardModel):
    """Plan milestone database model"""
    __tablename__ = "plan_milestone"
    
    plan_id = Column(UUID, ForeignKey("strategic_plan.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    target_date = Column(DateTime, nullable=False)
    actual_date = Column(DateTime, nullable=True)
    priority = enum_column(TaskPriority, default=TaskPriority.MEDIUM)
    criteria = Column(JSON, nullable=True)
    
    # Define enum columns for validation
    __enum_columns__ = {
        'priority': TaskPriority
    }
    
    # Relationships
    plan = relationship("StrategicPlanModel", back_populates="milestones")
    tasks = relationship("PlanningTaskModel", back_populates="milestone")
    
    def __repr__(self):
        return f"<PlanMilestoneModel(id='{self.id}', name='{self.name}', plan_id='{self.plan_id}')>"


class PlanningTaskModel(StandardModel):
    """Planning task database model"""
    __tablename__ = "planning_task"
    
    plan_id = Column(UUID, ForeignKey("strategic_plan.id"), nullable=False)
    phase_id = Column(UUID, ForeignKey("plan_phase.id"), nullable=True)
    milestone_id = Column(UUID, ForeignKey("plan_milestone.id"), nullable=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    estimated_duration = Column(Float, nullable=False)
    estimated_effort = Column(Float, nullable=False)
    required_skills = Column(JSON, nullable=True)
    constraints = Column(JSON, nullable=True)
    priority = enum_column(TaskPriority, default=TaskPriority.MEDIUM)
    status = enum_column(TaskStatus, default=TaskStatus.PENDING)
    earliest_start = Column(DateTime, nullable=True)
    earliest_finish = Column(DateTime, nullable=True)
    latest_start = Column(DateTime, nullable=True)
    latest_finish = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    actual_finish = Column(DateTime, nullable=True)
    is_critical_path = Column(Boolean, default=False)
    slack = Column(Float, nullable=True)
    acceptance_criteria = Column(JSON, nullable=True)
    assigned_to = Column(UUID, nullable=True)
    
    # Define enum columns for validation
    __enum_columns__ = {
        'priority': TaskPriority,
        'status': TaskStatus
    }
    
    # Relationships
    plan = relationship("StrategicPlanModel", back_populates="tasks")
    phase = relationship("PlanPhaseModel", back_populates="tasks")
    milestone = relationship("PlanMilestoneModel", back_populates="tasks")
    
    # Task dependencies (tasks that this task depends on)
    dependencies = relationship(
        "PlanningTaskModel",
        secondary=task_dependencies,
        primaryjoin=(id == task_dependencies.c.to_task_id),
        secondaryjoin=(id == task_dependencies.c.from_task_id),
        backref="dependent_tasks"
    )
    
    # Resource allocations
    resource_allocations = relationship("ResourceAllocationModel", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PlanningTaskModel(id='{self.id}', name='{self.name}', status='{self.status}')>"


class ResourceModel(StandardModel):
    """Resource database model"""
    __tablename__ = "resource"
    
    name = Column(String(200), nullable=False)
    resource_type = enum_column(ResourceType, nullable=False)
    description = Column(Text, nullable=True)
    skills = Column(JSON, nullable=True)
    availability = Column(JSON, nullable=True)
    capacity_hours = Column(Float, nullable=False, default=40.0)
    cost_rate = Column(Float, nullable=True)
    constraints = Column(JSON, nullable=True)
    external_id = Column(String(100), nullable=True)
    
    # Define enum columns for validation
    __enum_columns__ = {
        'resource_type': ResourceType
    }
    
    # Relationships
    allocations = relationship("ResourceAllocationModel", back_populates="resource", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ResourceModel(id='{self.id}', name='{self.name}', type='{self.resource_type}')>"


class ResourceAllocationModel(StandardModel):
    """Resource allocation database model"""
    __tablename__ = "resource_allocation"
    
    task_id = Column(UUID, ForeignKey("planning_task.id"), nullable=False)
    resource_id = Column(UUID, ForeignKey("resource.id"), nullable=False)
    allocation_percentage = Column(Float, nullable=False)
    assigned_hours = Column(Float, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_overallocated = Column(Boolean, default=False)
    
    # Relationships
    task = relationship("PlanningTaskModel", back_populates="resource_allocations")
    resource = relationship("ResourceModel", back_populates="allocations")
    
    def __repr__(self):
        return f"<ResourceAllocationModel(id='{self.id}', task_id='{self.task_id}', resource_id='{self.resource_id}')>"


class PlanTemplateModel(StandardModel):
    """Plan template database model"""
    __tablename__ = "plan_template"
    
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=False)
    structure = Column(JSON, nullable=False)
    customization_options = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    plans = relationship("StrategicPlanModel", back_populates="template")
    phases = relationship("TemplatePhaseModel", back_populates="template", cascade="all, delete-orphan")
    milestones = relationship("TemplateMilestoneModel", back_populates="template", cascade="all, delete-orphan")
    tasks = relationship("TemplateTaskModel", back_populates="template", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PlanTemplateModel(id='{self.id}', name='{self.name}', version='{self.version}')>"


class TemplatePhaseModel(StandardModel):
    """Template phase database model"""
    __tablename__ = "template_phase"
    
    template_id = Column(UUID, ForeignKey("plan_template.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, nullable=False, default=0)
    duration_estimate = Column(Float, nullable=True)
    objectives = Column(JSON, nullable=True)
    deliverables = Column(JSON, nullable=True)
    completion_criteria = Column(JSON, nullable=True)
    
    # Relationships
    template = relationship("PlanTemplateModel", back_populates="phases")
    tasks = relationship("TemplateTaskModel", back_populates="phase", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TemplatePhaseModel(id='{self.id}', name='{self.name}', template_id='{self.template_id}')>"


class TemplateMilestoneModel(StandardModel):
    """Template milestone database model"""
    __tablename__ = "template_milestone"
    
    template_id = Column(UUID, ForeignKey("plan_template.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    relative_day = Column(Integer, nullable=True)
    priority = enum_column(TaskPriority, default=TaskPriority.MEDIUM)
    criteria = Column(JSON, nullable=True)
    
    # Define enum columns for validation
    __enum_columns__ = {
        'priority': TaskPriority
    }
    
    # Relationships
    template = relationship("PlanTemplateModel", back_populates="milestones")
    tasks = relationship("TemplateTaskModel", back_populates="milestone", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TemplateMilestoneModel(id='{self.id}', name='{self.name}', template_id='{self.template_id}')>"


class TemplateTaskModel(StandardModel):
    """Template task database model"""
    __tablename__ = "template_task"
    
    template_id = Column(UUID, ForeignKey("plan_template.id"), nullable=False)
    phase_id = Column(UUID, ForeignKey("template_phase.id"), nullable=True)
    milestone_id = Column(UUID, ForeignKey("template_milestone.id"), nullable=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    estimated_duration = Column(Float, nullable=False)
    estimated_effort = Column(Float, nullable=False)
    required_skills = Column(JSON, nullable=True)
    priority = enum_column(TaskPriority, default=TaskPriority.MEDIUM)
    acceptance_criteria_template = Column(JSON, nullable=True)
    
    # Define enum columns for validation
    __enum_columns__ = {
        'priority': TaskPriority
    }
    
    # Relationships
    template = relationship("PlanTemplateModel", back_populates="tasks")
    phase = relationship("TemplatePhaseModel", back_populates="tasks")
    milestone = relationship("TemplateMilestoneModel", back_populates="tasks")
    
    # Template task dependencies
    dependencies = relationship(
        "TemplateTaskModel",
        secondary=Table(
            "template_task_dependency",
            StandardModel.metadata,
            Column("from_task_id", UUID, ForeignKey("template_task.id"), primary_key=True),
            Column("to_task_id", UUID, ForeignKey("template_task.id"), primary_key=True),
            Column("dependency_type", String(20), default=DependencyType.FINISH_TO_START.value),
            Column("lag", Float, default=0),
        ),
        primaryjoin=(id == Column("to_task_id")),
        secondaryjoin=(id == Column("from_task_id")),
        backref="dependent_tasks"
    )
    
    def __repr__(self):
        return f"<TemplateTaskModel(id='{self.id}', name='{self.name}', template_id='{self.template_id}')>"


class PlanningMethodologyModel(StandardModel):
    """Planning methodology database model"""
    __tablename__ = "planning_methodology"
    
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    methodology_type = Column(String(50), nullable=False)
    parameters = Column(JSON, nullable=False)
    constraints = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    plans = relationship("StrategicPlanModel", back_populates="methodology")
    
    def __repr__(self):
        return f"<PlanningMethodologyModel(id='{self.id}', name='{self.name}', type='{self.methodology_type}')>"


class TimelineForecastModel(StandardModel):
    """Timeline forecast database model"""
    __tablename__ = "timeline_forecast"
    
    plan_id = Column(UUID, ForeignKey("strategic_plan.id"), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    confidence_interval = Column(Float, nullable=False)
    timeline_data = Column(JSON, nullable=False)
    expected_completion = Column(DateTime, nullable=False)
    best_case_completion = Column(DateTime, nullable=False)
    worst_case_completion = Column(DateTime, nullable=False)
    
    # Relationships
    plan = relationship("StrategicPlanModel")
    
    def __repr__(self):
        return f"<TimelineForecastModel(id='{self.id}', plan_id='{self.plan_id}', generated_at='{self.generated_at}')>"


class BottleneckAnalysisModel(StandardModel):
    """Bottleneck analysis database model"""
    __tablename__ = "bottleneck_analysis"
    
    plan_id = Column(UUID, ForeignKey("strategic_plan.id"), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    bottlenecks = Column(JSON, nullable=False)
    recommendations = Column(JSON, nullable=False)
    impact_analysis = Column(JSON, nullable=False)
    
    # Relationships
    plan = relationship("StrategicPlanModel")
    
    def __repr__(self):
        return f"<BottleneckAnalysisModel(id='{self.id}', plan_id='{self.plan_id}', generated_at='{self.generated_at}')>"


class OptimizationResultModel(StandardModel):
    """Optimization result database model"""
    __tablename__ = "optimization_result"
    
    plan_id = Column(UUID, ForeignKey("strategic_plan.id"), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    optimization_target = enum_column(OptimizationTarget, nullable=False)
    status = Column(String(20), nullable=False)
    task_adjustments = Column(JSON, nullable=False)
    resource_assignments = Column(JSON, nullable=False)
    metrics = Column(JSON, nullable=False)
    improvements = Column(JSON, nullable=False)
    
    # Define enum columns for validation
    __enum_columns__ = {
        'optimization_target': OptimizationTarget
    }
    
    # Relationships
    plan = relationship("StrategicPlanModel")
    
    def __repr__(self):
        return f"<OptimizationResultModel(id='{self.id}', plan_id='{self.plan_id}', status='{self.status}')>"


class PlanHistoryModel(StandardModel):
    """Plan change history database model"""
    __tablename__ = "plan_history"
    
    plan_id = Column(UUID, ForeignKey("strategic_plan.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    previous_state = Column(JSON, nullable=True)
    new_state = Column(JSON, nullable=False)
    change_type = Column(String(50), nullable=False)
    change_reason = Column(Text, nullable=True)
    
    # Relationships
    plan = relationship("StrategicPlanModel")
    
    def __repr__(self):
        return f"<PlanHistoryModel(id='{self.id}', plan_id='{self.plan_id}', change_type='{self.change_type}')>"
