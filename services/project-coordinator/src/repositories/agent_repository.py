"""
Repository for agent-related database operations.

This module provides repository classes for accessing agent instructions,
capabilities, knowledge domains, and prompt templates from the database.
"""

from typing import Dict, List, Optional, Any, Union
from uuid import UUID
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..models.internal import (
    AgentInstructions, AgentCapability, AgentKnowledgeDomain, AgentRole,
    AgentPromptTemplate
)

logger = logging.getLogger(__name__)


class AgentRepository:
    """Repository for agent-related database operations."""

    def __init__(self, db: Session):
        """
        Initialize the repository with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_agent_instructions(self, agent_name: str) -> Optional[AgentInstructions]:
        """
        Get agent instructions by agent name.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            AgentInstructions object if found, None otherwise
        """
        try:
            return self.db.query(AgentInstructions).filter(
                AgentInstructions.agent_name == agent_name
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting agent instructions for {agent_name}: {e}")
            return None

    def get_agent_capabilities(self, agent_instruction_id: Union[str, UUID]) -> List[AgentCapability]:
        """
        Get agent capabilities by agent instruction ID.
        
        Args:
            agent_instruction_id: ID of the agent instructions
            
        Returns:
            List of AgentCapability objects
        """
        try:
            return self.db.query(AgentCapability).filter(
                AgentCapability.agent_instruction_id == agent_instruction_id
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting agent capabilities for {agent_instruction_id}: {e}")
            return []

    def get_agent_knowledge_domains(self, agent_instruction_id: Union[str, UUID]) -> List[AgentKnowledgeDomain]:
        """
        Get agent knowledge domains by agent instruction ID.
        
        Args:
            agent_instruction_id: ID of the agent instructions
            
        Returns:
            List of AgentKnowledgeDomain objects
        """
        try:
            return self.db.query(AgentKnowledgeDomain).filter(
                AgentKnowledgeDomain.agent_instruction_id == agent_instruction_id
            ).order_by(AgentKnowledgeDomain.priority_level).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting agent knowledge domains for {agent_instruction_id}: {e}")
            return []

    def get_agent_prompt_templates(
        self, agent_instruction_id: Union[str, UUID]
    ) -> List[AgentPromptTemplate]:
        """
        Get agent prompt templates by agent instruction ID.
        
        Args:
            agent_instruction_id: ID of the agent instructions
            
        Returns:
            List of AgentPromptTemplate objects
        """
        try:
            return self.db.query(AgentPromptTemplate).filter(
                AgentPromptTemplate.agent_instruction_id == agent_instruction_id
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting agent prompt templates for {agent_instruction_id}: {e}")
            return []

    def get_agent_prompt_template(
        self, agent_instruction_id: Union[str, UUID], template_name: str, 
        template_version: Optional[str] = None
    ) -> Optional[AgentPromptTemplate]:
        """
        Get a specific agent prompt template.
        
        Args:
            agent_instruction_id: ID of the agent instructions
            template_name: Name of the template
            template_version: Version of the template (optional, gets latest if not specified)
            
        Returns:
            AgentPromptTemplate object if found, None otherwise
        """
        try:
            query = self.db.query(AgentPromptTemplate).filter(
                AgentPromptTemplate.agent_instruction_id == agent_instruction_id,
                AgentPromptTemplate.template_name == template_name
            )
            
            if template_version:
                return query.filter(
                    AgentPromptTemplate.template_version == template_version
                ).first()
            else:
                # Get the latest version
                return query.order_by(
                    AgentPromptTemplate.template_version.desc()
                ).first()
        except SQLAlchemyError as e:
            logger.error(
                f"Error getting agent prompt template {template_name} "
                f"for {agent_instruction_id}: {e}"
            )
            return None

    def get_complete_agent_configuration(self, agent_name: str) -> Dict[str, Any]:
        """
        Get complete agent configuration including instructions, capabilities,
        knowledge domains, and prompt templates.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dictionary containing complete agent configuration
        """
        try:
            agent_instructions = self.get_agent_instructions(agent_name)
            if not agent_instructions:
                logger.warning(f"Agent instructions not found for {agent_name}")
                return {}
            
            agent_capabilities = self.get_agent_capabilities(agent_instructions.id)
            agent_knowledge_domains = self.get_agent_knowledge_domains(agent_instructions.id)
            agent_prompt_templates = self.get_agent_prompt_templates(agent_instructions.id)
            
            # Convert to dictionary
            capabilities_dict = {
                cap.capability_name: {
                    "description": cap.description,
                    "parameters": cap.parameters
                } for cap in agent_capabilities
            }
            
            knowledge_domains_dict = {
                domain.domain_name: {
                    "priority_level": domain.priority_level,
                    "description": domain.description
                } for domain in agent_knowledge_domains
            }
            
            prompt_templates_dict = {
                template.template_name: {
                    "version": template.template_version,
                    "content": template.template_content,
                    "context_parameters": template.context_parameters
                } for template in agent_prompt_templates
            }
            
            return {
                "agent_name": agent_instructions.agent_name,
                "purpose": agent_instructions.purpose,
                "capabilities": capabilities_dict,
                "tone_guidelines": agent_instructions.tone_guidelines,
                "knowledge_domains": knowledge_domains_dict,
                "response_templates": agent_instructions.response_templates,
                "prompt_templates": prompt_templates_dict,
                "created_at": agent_instructions.created_at,
                "updated_at": agent_instructions.updated_at
            }
        except SQLAlchemyError as e:
            logger.error(f"Error getting complete agent configuration for {agent_name}: {e}")
            return {}
