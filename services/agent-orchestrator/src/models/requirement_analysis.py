"""
Requirement analysis models.

This module contains models for requirement analysis functionality.
"""

from typing import List, Dict, Optional, Any, Set
from uuid import UUID
from pydantic import Field, validator

from shared.models.src.base import BaseModel, BaseEntityModel, BaseTimestampModel
from shared.models.src.api.responses import create_data_response_model, create_list_response_model
from shared.models.src.enums import AgentType


class RequirementCategory(str):
    """
    Requirement category.
    """
    FUNCTIONAL = "FUNCTIONAL"
    NON_FUNCTIONAL = "NON_FUNCTIONAL"
    DOMAIN_SPECIFIC = "DOMAIN_SPECIFIC"
    TECHNICAL = "TECHNICAL"
    INTEGRATION = "INTEGRATION"
    COLLABORATION = "COLLABORATION"


class RequirementPriority(str):
    """
    Requirement priority.
    """
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RequirementAnalysisRequest(BaseModel):
    """
    Model for requirement analysis request.
    """
    project_id: UUID
    description: str
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "description": "Create a web application for managing inventory with real-time updates and reporting features.",
                "context": {
                    "domain": "Inventory Management",
                    "target_users": ["Warehouse Managers", "Inventory Clerks"],
                    "existing_systems": ["ERP System", "Warehouse Management System"]
                }
            }
        }


class RequirementItem(BaseModel):
    """
    Model for a single requirement item.
    """
    id: str
    description: str
    category: str
    priority: str
    agent_types: List[AgentType]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "id": "REQ-001",
                "description": "The system must provide real-time inventory updates",
                "category": "FUNCTIONAL",
                "priority": "HIGH",
                "agent_types": ["DEVELOPER", "SPECIALIST"],
                "metadata": {
                    "source": "project_description",
                    "confidence": 0.85
                }
            }
        }


class AgentSpecializationRequirement(BaseModel):
    """
    Model for agent specialization requirement.
    """
    agent_type: AgentType
    required_skills: List[str]
    responsibilities: List[str]
    knowledge_domains: List[str]
    collaboration_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        schema_extra = {
            "example": {
                "agent_type": "DEVELOPER",
                "required_skills": ["Web Development", "Database Design", "API Integration"],
                "responsibilities": ["Implement inventory tracking features", "Create database schema"],
                "knowledge_domains": ["Inventory Management", "Web Technologies"],
                "collaboration_patterns": [
                    {
                        "collaborator_type": "DESIGNER",
                        "interaction_type": "REQUEST_REVIEW",
                        "description": "Request UI design review"
                    }
                ]
            }
        }


class RequirementAnalysisResult(BaseModel):
    """
    Model for requirement analysis result.
    """
    project_id: UUID
    requirements: List[RequirementItem]
    agent_specializations: List[AgentSpecializationRequirement]
    requirement_categories: Dict[str, int]  # Count of requirements by category
    requirement_priorities: Dict[str, int]  # Count of requirements by priority
    collaboration_graph: Dict[str, List[str]]  # Agent type to list of collaborator types
    
    class Config:
        schema_extra = {
            "example": {
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "requirements": [
                    {
                        "id": "REQ-001",
                        "description": "The system must provide real-time inventory updates",
                        "category": "FUNCTIONAL",
                        "priority": "HIGH",
                        "agent_types": ["DEVELOPER", "SPECIALIST"],
                        "metadata": {
                            "source": "project_description",
                            "confidence": 0.85
                        }
                    }
                ],
                "agent_specializations": [
                    {
                        "agent_type": "DEVELOPER",
                        "required_skills": ["Web Development", "Database Design", "API Integration"],
                        "responsibilities": ["Implement inventory tracking features", "Create database schema"],
                        "knowledge_domains": ["Inventory Management", "Web Technologies"],
                        "collaboration_patterns": [
                            {
                                "collaborator_type": "DESIGNER",
                                "interaction_type": "REQUEST_REVIEW",
                                "description": "Request UI design review"
                            }
                        ]
                    }
                ],
                "requirement_categories": {
                    "FUNCTIONAL": 5,
                    "NON_FUNCTIONAL": 2,
                    "DOMAIN_SPECIFIC": 3
                },
                "requirement_priorities": {
                    "HIGH": 4,
                    "MEDIUM": 5,
                    "LOW": 1
                },
                "collaboration_graph": {
                    "DEVELOPER": ["DESIGNER", "SPECIALIST"],
                    "DESIGNER": ["DEVELOPER"],
                    "SPECIALIST": ["DEVELOPER", "COORDINATOR"]
                }
            }
        }


# Create response models using shared utilities
RequirementAnalysisResponse = create_data_response_model(RequirementAnalysisResult)
