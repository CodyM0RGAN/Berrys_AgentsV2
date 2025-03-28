"""
Agent Template Engine models.

This module contains models for the Agent Template Engine functionality.
"""

from typing import List, Dict, Optional, Any
from uuid import UUID
from enum import Enum
from pydantic import Field, validator
from datetime import datetime

from shared.models.src.base import BaseModel, BaseEntityModel, BaseTimestampModel
from shared.models.src.api.responses import create_data_response_model, create_list_response_model
from shared.models.src.enums import AgentType


class TemplateType(str, Enum):
    """
    Type of agent template.
    """
    SYSTEM = "SYSTEM"  # Built-in system templates
    CUSTOM = "CUSTOM"  # User-created templates
    SPECIALIZED = "SPECIALIZED"  # Templates for specialized agents
    PROJECT = "PROJECT"  # Project-specific templates


class AgentTemplateBase(BaseModel):
    """
    Base model for agent template.
    """
    name: str
    description: Optional[str] = None
    template_type: str
    base_agent_type: str
    template_content: Dict[str, Any] = Field(default_factory=dict)
    category: Optional[str] = None
    is_system_template: bool = False
    is_public: bool = False
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Developer Agent Template",
                "description": "Template for developer agents",
                "template_type": "SYSTEM",
                "base_agent_type": "DEVELOPER",
                "template_content": {
                    "skills": ["Programming", "Debugging", "Code Review"],
                    "tools": ["Git", "IDE", "Compiler"],
                    "prompt_template": "You are a developer agent specialized in {specialization}...",
                    "behavior": {
                        "communication_style": "technical",
                        "problem_solving_approach": "analytical"
                    }
                },
                "category": "Development",
                "is_system_template": True,
                "is_public": True
            }
        }


class AgentTemplateCreate(AgentTemplateBase):
    """
    Model for creating an agent template.
    """
    owner_id: Optional[UUID] = None


class AgentTemplateUpdate(BaseModel):
    """
    Model for updating an agent template.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    template_content: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    is_public: Optional[bool] = None
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Updated Developer Template",
                "description": "Updated template for developer agents",
                "template_content": {
                    "skills": ["Programming", "Debugging", "Code Review", "Testing"],
                    "tools": ["Git", "IDE", "Compiler", "Debugger"],
                    "prompt_template": "You are a developer agent specialized in {specialization}...",
                    "behavior": {
                        "communication_style": "technical",
                        "problem_solving_approach": "analytical"
                    }
                },
                "category": "Software Development",
                "is_public": True
            }
        }


class AgentTemplate(AgentTemplateBase, BaseEntityModel, BaseTimestampModel):
    """
    Model for an agent template.
    """
    id: UUID
    owner_id: Optional[UUID] = None
    checksum: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Developer Agent Template",
                "description": "Template for developer agents",
                "template_type": "SYSTEM",
                "base_agent_type": "DEVELOPER",
                "template_content": {
                    "skills": ["Programming", "Debugging", "Code Review"],
                    "tools": ["Git", "IDE", "Compiler"],
                    "prompt_template": "You are a developer agent specialized in {specialization}...",
                    "behavior": {
                        "communication_style": "technical",
                        "problem_solving_approach": "analytical"
                    }
                },
                "category": "Development",
                "is_system_template": True,
                "is_public": True,
                "owner_id": "123e4567-e89b-12d3-a456-426614174001",
                "checksum": "a1b2c3d4e5f6",
                "created_at": "2025-03-28T12:00:00Z",
                "updated_at": "2025-03-28T12:00:00Z"
            }
        }


class AgentTemplateVersion(BaseEntityModel, BaseTimestampModel):
    """
    Model for an agent template version.
    """
    id: UUID
    template_id: UUID
    version_number: int
    template_content: Dict[str, Any] = Field(default_factory=dict)
    changelog: Optional[str] = None
    created_by: Optional[UUID] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174002",
                "template_id": "123e4567-e89b-12d3-a456-426614174000",
                "version_number": 1,
                "template_content": {
                    "skills": ["Programming", "Debugging"],
                    "tools": ["Git", "IDE"],
                    "prompt_template": "You are a developer agent...",
                    "behavior": {
                        "communication_style": "technical",
                        "problem_solving_approach": "analytical"
                    }
                },
                "changelog": "Initial version",
                "created_by": "123e4567-e89b-12d3-a456-426614174001",
                "created_at": "2025-03-28T12:00:00Z",
                "updated_at": "2025-03-28T12:00:00Z"
            }
        }


class TemplateTag(BaseEntityModel, BaseTimestampModel):
    """
    Model for a template tag.
    """
    id: UUID
    name: str
    description: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174003",
                "name": "Development",
                "description": "Templates for development tasks",
                "created_at": "2025-03-28T12:00:00Z",
                "updated_at": "2025-03-28T12:00:00Z"
            }
        }


class TemplateTagCreate(BaseModel):
    """
    Model for creating a template tag.
    """
    name: str
    description: Optional[str] = None


class TemplateTagUpdate(BaseModel):
    """
    Model for updating a template tag.
    """
    name: Optional[str] = None
    description: Optional[str] = None


class TemplateAnalytics(BaseModel):
    """
    Model for template analytics.
    """
    template_id: UUID
    usage_count: int = 0
    last_used: Optional[datetime] = None
    success_rate: Optional[float] = None
    
    class Config:
        schema_extra = {
            "example": {
                "template_id": "123e4567-e89b-12d3-a456-426614174000",
                "usage_count": 42,
                "last_used": "2025-03-28T12:00:00Z",
                "success_rate": 0.95
            }
        }


class TemplateCustomizationOption(BaseModel):
    """
    Model for a template customization option.
    """
    key: str
    name: str
    description: str = ""
    option_type: str  # "text", "boolean", "select", "number"
    default_value: Any = None
    allowed_values: Optional[List[Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "key": "communication_style",
                "name": "Communication Style",
                "description": "The communication style of the agent",
                "option_type": "select",
                "default_value": "technical",
                "allowed_values": ["technical", "casual", "formal"]
            }
        }


class TemplateCustomization(BaseModel):
    """
    Model for template customization.
    """
    template_id: UUID
    customization_values: Dict[str, Any] = Field(default_factory=dict)
    name: Optional[str] = None
    description: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "template_id": "123e4567-e89b-12d3-a456-426614174000",
                "customization_values": {
                    "communication_style": "casual",
                    "problem_solving_approach": "creative",
                    "specialization": "Web Development"
                },
                "name": "Web Developer Template",
                "description": "Customized template for web developers"
            }
        }


class TemplateImportSource(BaseModel):
    """
    Model for template import source.
    """
    source_type: str  # "file", "directory", "url"
    source_path: str
    is_system_template: bool = False
    
    class Config:
        schema_extra = {
            "example": {
                "source_type": "directory",
                "source_path": "/path/to/templates",
                "is_system_template": True
            }
        }


class VersionComparisonResult(BaseModel):
    """
    Model for version comparison result.
    """
    template_id: UUID
    version1: int
    version2: int
    differences: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "template_id": "123e4567-e89b-12d3-a456-426614174000",
                "version1": 1,
                "version2": 2,
                "differences": {
                    "added": ["skills.Testing"],
                    "removed": [],
                    "changed": ["prompt_template"]
                }
            }
        }


# Create response models using shared utilities
AgentTemplateResponse = create_data_response_model(AgentTemplate)
AgentTemplateListResponse = create_list_response_model(AgentTemplate)
AgentTemplateVersionResponse = create_data_response_model(AgentTemplateVersion)
AgentTemplateVersionListResponse = create_list_response_model(AgentTemplateVersion)
TemplateTagResponse = create_data_response_model(TemplateTag)
TemplateTagListResponse = create_list_response_model(TemplateTag)
TemplateAnalyticsResponse = create_data_response_model(TemplateAnalytics)
VersionComparisonResultResponse = create_data_response_model(VersionComparisonResult)
