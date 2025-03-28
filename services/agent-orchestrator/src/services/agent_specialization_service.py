"""
Agent specialization service.

This module contains the service for managing agent specializations.
"""

import logging
from sqlalchemy import select, func, or_, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional, Any, Tuple
from uuid import UUID

from shared.utils.src.messaging import EventBus, CommandBus
from shared.models.src.enums import AgentType

from ..config import AgentOrchestratorConfig
from ..exceptions import (
    SpecializationNotFoundError,
    DatabaseError,
)
from ..models.requirement_analysis import (
    AgentSpecializationRequirement,
)

logger = logging.getLogger(__name__)


class AgentSpecializationService:
    """
    Service for agent specialization operations.
    """
    
    def __init__(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        command_bus: CommandBus,
        settings: AgentOrchestratorConfig,
    ):
        """
        Initialize the agent specialization service.
        
        Args:
            db: Database session
            event_bus: Event bus
            command_bus: Command bus
            settings: Application settings
        """
        self.db = db
        self.event_bus = event_bus
        self.command_bus = command_bus
        self.settings = settings
    
    async def get_agent_specialization(
        self,
        agent_type: AgentType,
    ) -> Optional[AgentSpecializationRequirement]:
        """
        Get agent specialization by agent type.
        
        Args:
            agent_type: Agent type
            
        Returns:
            Optional[AgentSpecializationRequirement]: Agent specialization if found, None otherwise
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Query agent specialization
            query = """
            SELECT 
                s.agent_type,
                s.required_skills,
                s.responsibilities,
                s.knowledge_domains,
                json_agg(
                    json_build_object(
                        'collaborator_type', p.collaborator_type,
                        'interaction_type', p.interaction_type,
                        'description', p.description
                    )
                ) AS collaboration_patterns
            FROM 
                agent_specialization s
            LEFT JOIN 
                agent_collaboration_pattern p ON s.id = p.agent_specialization_id
            WHERE 
                s.agent_type = :agent_type
            GROUP BY 
                s.id, s.agent_type, s.required_skills, s.responsibilities, s.knowledge_domains
            """
            
            # Execute query
            result = await self.db.execute(
                text(query),
                {"agent_type": agent_type.value},
            )
            
            # Get first row
            row = result.fetchone()
            
            # Return None if not found
            if not row:
                return None
            
            # Create specialization requirement
            specialization = AgentSpecializationRequirement(
                agent_type=agent_type,
                required_skills=row.required_skills,
                responsibilities=row.responsibilities,
                knowledge_domains=row.knowledge_domains,
                collaboration_patterns=row.collaboration_patterns,
            )
            
            return specialization
        except Exception as e:
            logger.error(f"Error getting agent specialization for {agent_type}: {str(e)}")
            raise DatabaseError(f"Failed to get agent specialization: {str(e)}")
    
    async def list_agent_specializations(
        self,
    ) -> List[AgentSpecializationRequirement]:
        """
        List all agent specializations.
        
        Returns:
            List[AgentSpecializationRequirement]: List of agent specializations
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Query agent specializations
            query = """
            SELECT 
                s.agent_type,
                s.required_skills,
                s.responsibilities,
                s.knowledge_domains,
                json_agg(
                    json_build_object(
                        'collaborator_type', p.collaborator_type,
                        'interaction_type', p.interaction_type,
                        'description', p.description
                    )
                ) AS collaboration_patterns
            FROM 
                agent_specialization s
            LEFT JOIN 
                agent_collaboration_pattern p ON s.id = p.agent_specialization_id
            GROUP BY 
                s.id, s.agent_type, s.required_skills, s.responsibilities, s.knowledge_domains
            """
            
            # Execute query
            result = await self.db.execute(text(query))
            
            # Get all rows
            rows = result.fetchall()
            
            # Create specialization requirements
            specializations = []
            for row in rows:
                agent_type = AgentType(row.agent_type)
                specialization = AgentSpecializationRequirement(
                    agent_type=agent_type,
                    required_skills=row.required_skills,
                    responsibilities=row.responsibilities,
                    knowledge_domains=row.knowledge_domains,
                    collaboration_patterns=row.collaboration_patterns,
                )
                specializations.append(specialization)
            
            return specializations
        except Exception as e:
            logger.error(f"Error listing agent specializations: {str(e)}")
            raise DatabaseError(f"Failed to list agent specializations: {str(e)}")
    
    async def create_agent_specialization(
        self,
        specialization: AgentSpecializationRequirement,
    ) -> AgentSpecializationRequirement:
        """
        Create a new agent specialization.
        
        Args:
            specialization: Agent specialization
            
        Returns:
            AgentSpecializationRequirement: Created specialization
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Begin transaction
            async with self.db.begin():
                # Insert agent specialization
                insert_specialization_query = """
                INSERT INTO agent_specialization (
                    agent_type,
                    required_skills,
                    responsibilities,
                    knowledge_domains
                )
                VALUES (
                    :agent_type,
                    :required_skills,
                    :responsibilities,
                    :knowledge_domains
                )
                RETURNING id
                """
                
                # Execute query
                result = await self.db.execute(
                    text(insert_specialization_query),
                    {
                        "agent_type": specialization.agent_type.value,
                        "required_skills": specialization.required_skills,
                        "responsibilities": specialization.responsibilities,
                        "knowledge_domains": specialization.knowledge_domains,
                    },
                )
                
                # Get specialization ID
                specialization_id = result.scalar_one()
                
                # Insert collaboration patterns
                if specialization.collaboration_patterns:
                    for pattern in specialization.collaboration_patterns:
                        insert_pattern_query = """
                        INSERT INTO agent_collaboration_pattern (
                            agent_specialization_id,
                            collaborator_type,
                            interaction_type,
                            description
                        )
                        VALUES (
                            :agent_specialization_id,
                            :collaborator_type,
                            :interaction_type,
                            :description
                        )
                        """
                        
                        # Execute query
                        await self.db.execute(
                            text(insert_pattern_query),
                            {
                                "agent_specialization_id": specialization_id,
                                "collaborator_type": pattern.get("collaborator_type"),
                                "interaction_type": pattern.get("interaction_type"),
                                "description": pattern.get("description"),
                            },
                        )
            
            # Publish event
            await self.event_bus.publish_event(
                "agent.specialization.created",
                {
                    "agent_type": specialization.agent_type.value,
                }
            )
            
            return specialization
        except Exception as e:
            logger.error(f"Error creating agent specialization: {str(e)}")
            raise DatabaseError(f"Failed to create agent specialization: {str(e)}")
    
    async def update_agent_specialization(
        self,
        agent_type: AgentType,
        specialization: AgentSpecializationRequirement,
    ) -> AgentSpecializationRequirement:
        """
        Update an agent specialization.
        
        Args:
            agent_type: Agent type
            specialization: Agent specialization
            
        Returns:
            AgentSpecializationRequirement: Updated specialization
            
        Raises:
            SpecializationNotFoundError: If specialization not found
            DatabaseError: If database operation fails
        """
        try:
            # Begin transaction
            async with self.db.begin():
                # Get specialization ID
                get_id_query = """
                SELECT id FROM agent_specialization WHERE agent_type = :agent_type
                """
                
                # Execute query
                result = await self.db.execute(
                    text(get_id_query),
                    {"agent_type": agent_type.value},
                )
                
                # Get specialization ID
                specialization_id = result.scalar_one_or_none()
                
                # Check if specialization exists
                if not specialization_id:
                    raise SpecializationNotFoundError(agent_type.value)
                
                # Update agent specialization
                update_specialization_query = """
                UPDATE agent_specialization
                SET
                    required_skills = :required_skills,
                    responsibilities = :responsibilities,
                    knowledge_domains = :knowledge_domains,
                    updated_at = now()
                WHERE
                    id = :id
                """
                
                # Execute query
                await self.db.execute(
                    text(update_specialization_query),
                    {
                        "id": specialization_id,
                        "required_skills": specialization.required_skills,
                        "responsibilities": specialization.responsibilities,
                        "knowledge_domains": specialization.knowledge_domains,
                    },
                )
                
                # Delete existing collaboration patterns
                delete_patterns_query = """
                DELETE FROM agent_collaboration_pattern
                WHERE agent_specialization_id = :agent_specialization_id
                """
                
                # Execute query
                await self.db.execute(
                    text(delete_patterns_query),
                    {"agent_specialization_id": specialization_id},
                )
                
                # Insert new collaboration patterns
                if specialization.collaboration_patterns:
                    for pattern in specialization.collaboration_patterns:
                        insert_pattern_query = """
                        INSERT INTO agent_collaboration_pattern (
                            agent_specialization_id,
                            collaborator_type,
                            interaction_type,
                            description
                        )
                        VALUES (
                            :agent_specialization_id,
                            :collaborator_type,
                            :interaction_type,
                            :description
                        )
                        """
                        
                        # Execute query
                        await self.db.execute(
                            text(insert_pattern_query),
                            {
                                "agent_specialization_id": specialization_id,
                                "collaborator_type": pattern.get("collaborator_type"),
                                "interaction_type": pattern.get("interaction_type"),
                                "description": pattern.get("description"),
                            },
                        )
            
            # Publish event
            await self.event_bus.publish_event(
                "agent.specialization.updated",
                {
                    "agent_type": specialization.agent_type.value,
                }
            )
            
            return specialization
        except SpecializationNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating agent specialization: {str(e)}")
            raise DatabaseError(f"Failed to update agent specialization: {str(e)}")
    
    async def delete_agent_specialization(
        self,
        agent_type: AgentType,
    ) -> None:
        """
        Delete an agent specialization.
        
        Args:
            agent_type: Agent type
            
        Raises:
            SpecializationNotFoundError: If specialization not found
            DatabaseError: If database operation fails
        """
        try:
            # Begin transaction
            async with self.db.begin():
                # Get specialization ID
                get_id_query = """
                SELECT id FROM agent_specialization WHERE agent_type = :agent_type
                """
                
                # Execute query
                result = await self.db.execute(
                    text(get_id_query),
                    {"agent_type": agent_type.value},
                )
                
                # Get specialization ID
                specialization_id = result.scalar_one_or_none()
                
                # Check if specialization exists
                if not specialization_id:
                    raise SpecializationNotFoundError(agent_type.value)
                
                # Delete agent specialization
                delete_specialization_query = """
                DELETE FROM agent_specialization
                WHERE id = :id
                """
                
                # Execute query
                await self.db.execute(
                    text(delete_specialization_query),
                    {"id": specialization_id},
                )
            
            # Publish event
            await self.event_bus.publish_event(
                "agent.specialization.deleted",
                {
                    "agent_type": agent_type.value,
                }
            )
        except SpecializationNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting agent specialization: {str(e)}")
            raise DatabaseError(f"Failed to delete agent specialization: {str(e)}")
