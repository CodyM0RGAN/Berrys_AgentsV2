"""
Collaboration pattern service.

This module contains the service for identifying and managing collaboration patterns
between agents.
"""

import logging
import json
from sqlalchemy import select, func, or_, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional, Any, Set, Tuple
from uuid import UUID

from shared.utils.src.messaging import EventBus, CommandBus
from shared.models.src.enums import AgentType

from ..config import AgentOrchestratorConfig
from ..exceptions import (
    DatabaseError,
    AgentNotFoundError,
    PatternNotFoundError,
)
from ..models.requirement_analysis import (
    AgentSpecializationRequirement,
    RequirementItem,
)
from ..models.collaboration_pattern import (
    CollaborationPattern,
    CollaborationPatternCreate,
    CollaborationPatternUpdate,
    CollaborationGraph,
    CollaborationGraphNode,
    CollaborationGraphEdge,
)
from .agent_specialization_service import AgentSpecializationService

logger = logging.getLogger(__name__)


class CollaborationPatternService:
    """
    Service for collaboration pattern operations.
    """
    
    def __init__(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        command_bus: CommandBus,
        settings: AgentOrchestratorConfig,
        agent_specialization_service: Optional[AgentSpecializationService] = None,
        enhanced_communication_service = None,
    ):
        """
        Initialize the collaboration pattern service.
        
        Args:
            db: Database session
            event_bus: Event bus
            command_bus: Command bus
            settings: Application settings
            agent_specialization_service: Agent specialization service
            enhanced_communication_service: Enhanced communication service
        """
        self.db = db
        self.event_bus = event_bus
        self.command_bus = command_bus
        self.settings = settings
        self.agent_specialization_service = agent_specialization_service or AgentSpecializationService(
            db=db,
            event_bus=event_bus,
            command_bus=command_bus,
            settings=settings,
        )
        self.enhanced_communication_service = enhanced_communication_service
    
    async def list_patterns(
        self,
        source_agent_type: Optional[AgentType] = None,
        target_agent_type: Optional[AgentType] = None,
        interaction_type: Optional[str] = None,
    ) -> List[CollaborationPattern]:
        """
        List collaboration patterns with optional filtering.
        
        Args:
            source_agent_type: Filter by source agent type
            target_agent_type: Filter by target agent type
            interaction_type: Filter by interaction type
            
        Returns:
            List[CollaborationPattern]: List of collaboration patterns
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Build query
            query = """
            SELECT 
                p.id,
                p.source_agent_type,
                p.target_agent_type,
                p.interaction_type,
                p.description,
                p.priority,
                p.metadata,
                p.source_agent_id,
                p.target_agent_id,
                p.created_at,
                p.updated_at
            FROM 
                collaboration_pattern p
            WHERE 
                1=1
            """
            
            # Add filters
            params = {}
            if source_agent_type:
                query += " AND p.source_agent_type = :source_agent_type"
                params["source_agent_type"] = source_agent_type.value
            
            if target_agent_type:
                query += " AND p.target_agent_type = :target_agent_type"
                params["target_agent_type"] = target_agent_type.value
            
            if interaction_type:
                query += " AND p.interaction_type = :interaction_type"
                params["interaction_type"] = interaction_type
            
            # Add order by
            query += " ORDER BY p.created_at DESC"
            
            # Execute query
            result = await self.db.execute(text(query), params)
            
            # Get all rows
            rows = result.fetchall()
            
            # Create patterns
            patterns = []
            for row in rows:
                pattern = CollaborationPattern(
                    id=row.id,
                    source_agent_type=row.source_agent_type,
                    target_agent_type=row.target_agent_type,
                    interaction_type=row.interaction_type,
                    description=row.description,
                    priority=row.priority,
                    metadata=row.metadata,
                    source_agent_id=row.source_agent_id,
                    target_agent_id=row.target_agent_id,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                )
                patterns.append(pattern)
            
            return patterns
        except Exception as e:
            logger.error(f"Error listing collaboration patterns: {str(e)}")
            raise DatabaseError(f"Failed to list collaboration patterns: {str(e)}")
    
    async def get_pattern(
        self,
        pattern_id: UUID,
    ) -> Optional[CollaborationPattern]:
        """
        Get a collaboration pattern by ID.
        
        Args:
            pattern_id: Collaboration pattern ID
            
        Returns:
            Optional[CollaborationPattern]: Collaboration pattern if found, None otherwise
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Query pattern
            query = """
            SELECT 
                p.id,
                p.source_agent_type,
                p.target_agent_type,
                p.interaction_type,
                p.description,
                p.priority,
                p.metadata,
                p.source_agent_id,
                p.target_agent_id,
                p.created_at,
                p.updated_at
            FROM 
                collaboration_pattern p
            WHERE 
                p.id = :pattern_id
            """
            
            # Execute query
            result = await self.db.execute(
                text(query),
                {"pattern_id": pattern_id},
            )
            
            # Get first row
            row = result.fetchone()
            
            # Return None if not found
            if not row:
                return None
            
            # Create pattern
            pattern = CollaborationPattern(
                id=row.id,
                source_agent_type=row.source_agent_type,
                target_agent_type=row.target_agent_type,
                interaction_type=row.interaction_type,
                description=row.description,
                priority=row.priority,
                metadata=row.metadata,
                source_agent_id=row.source_agent_id,
                target_agent_id=row.target_agent_id,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            
            return pattern
        except Exception as e:
            logger.error(f"Error getting collaboration pattern: {str(e)}")
            raise DatabaseError(f"Failed to get collaboration pattern: {str(e)}")
    
    async def create_pattern(
        self,
        pattern: CollaborationPatternCreate,
    ) -> CollaborationPattern:
        """
        Create a new collaboration pattern.
        
        Args:
            pattern: Collaboration pattern to create
            
        Returns:
            CollaborationPattern: Created collaboration pattern
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Begin transaction
            async with self.db.begin():
                # Insert pattern
                insert_query = """
                INSERT INTO collaboration_pattern (
                    source_agent_type,
                    target_agent_type,
                    interaction_type,
                    description,
                    priority,
                    metadata
                )
                VALUES (
                    :source_agent_type,
                    :target_agent_type,
                    :interaction_type,
                    :description,
                    :priority,
                    :metadata
                )
                RETURNING 
                    id,
                    source_agent_type,
                    target_agent_type,
                    interaction_type,
                    description,
                    priority,
                    metadata,
                    source_agent_id,
                    target_agent_id,
                    created_at,
                    updated_at
                """
                
                # Execute query
                result = await self.db.execute(
                    text(insert_query),
                    {
                        "source_agent_type": pattern.source_agent_type,
                        "target_agent_type": pattern.target_agent_type,
                        "interaction_type": pattern.interaction_type,
                        "description": pattern.description,
                        "priority": pattern.priority,
                        "metadata": json.dumps(pattern.metadata),
                    },
                )
                
                # Get inserted row
                row = result.fetchone()
                
                # Create pattern
                created_pattern = CollaborationPattern(
                    id=row.id,
                    source_agent_type=row.source_agent_type,
                    target_agent_type=row.target_agent_type,
                    interaction_type=row.interaction_type,
                    description=row.description,
                    priority=row.priority,
                    metadata=row.metadata,
                    source_agent_id=row.source_agent_id,
                    target_agent_id=row.target_agent_id,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                )
            
            # Publish event
            await self.event_bus.publish_event(
                "agent.collaboration_pattern.created",
                {
                    "pattern_id": str(created_pattern.id),
                    "source_agent_type": created_pattern.source_agent_type,
                    "target_agent_type": created_pattern.target_agent_type,
                }
            )
            
            return created_pattern
        except Exception as e:
            logger.error(f"Error creating collaboration pattern: {str(e)}")
            raise DatabaseError(f"Failed to create collaboration pattern: {str(e)}")
    
    async def update_pattern(
        self,
        pattern_id: UUID,
        pattern: CollaborationPatternUpdate,
    ) -> CollaborationPattern:
        """
        Update a collaboration pattern.
        
        Args:
            pattern_id: Collaboration pattern ID
            pattern: Collaboration pattern update data
            
        Returns:
            CollaborationPattern: Updated collaboration pattern
            
        Raises:
            PatternNotFoundError: If pattern not found
            DatabaseError: If database operation fails
        """
        try:
            # Begin transaction
            async with self.db.begin():
                # Check if pattern exists
                check_query = "SELECT 1 FROM collaboration_pattern WHERE id = :pattern_id"
                result = await self.db.execute(text(check_query), {"pattern_id": pattern_id})
                if not result.scalar_one_or_none():
                    raise PatternNotFoundError(pattern_id)
                
                # Build update query
                update_query = "UPDATE collaboration_pattern SET "
                update_parts = []
                params = {"pattern_id": pattern_id}
                
                # Add update parts
                if pattern.target_agent_type is not None:
                    update_parts.append("target_agent_type = :target_agent_type")
                    params["target_agent_type"] = pattern.target_agent_type
                
                if pattern.interaction_type is not None:
                    update_parts.append("interaction_type = :interaction_type")
                    params["interaction_type"] = pattern.interaction_type
                
                if pattern.description is not None:
                    update_parts.append("description = :description")
                    params["description"] = pattern.description
                
                if pattern.priority is not None:
                    update_parts.append("priority = :priority")
                    params["priority"] = pattern.priority
                
                if pattern.metadata is not None:
                    update_parts.append("metadata = :metadata")
                    params["metadata"] = json.dumps(pattern.metadata)
                
                # Add updated_at
                update_parts.append("updated_at = now()")
                
                # Complete query
                update_query += ", ".join(update_parts)
                update_query += " WHERE id = :pattern_id"
                
                # Execute update
                await self.db.execute(text(update_query), params)
                
                # Get updated pattern
                get_query = """
                SELECT 
                    p.id,
                    p.source_agent_type,
                    p.target_agent_type,
                    p.interaction_type,
                    p.description,
                    p.priority,
                    p.metadata,
                    p.source_agent_id,
                    p.target_agent_id,
                    p.created_at,
                    p.updated_at
                FROM 
                    collaboration_pattern p
                WHERE 
                    p.id = :pattern_id
                """
                
                # Execute query
                result = await self.db.execute(
                    text(get_query),
                    {"pattern_id": pattern_id},
                )
                
                # Get first row
                row = result.fetchone()
                
                # Create pattern
                updated_pattern = CollaborationPattern(
                    id=row.id,
                    source_agent_type=row.source_agent_type,
                    target_agent_type=row.target_agent_type,
                    interaction_type=row.interaction_type,
                    description=row.description,
                    priority=row.priority,
                    metadata=row.metadata,
                    source_agent_id=row.source_agent_id,
                    target_agent_id=row.target_agent_id,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                )
            
            # Publish event
            await self.event_bus.publish_event(
                "agent.collaboration_pattern.updated",
                {
                    "pattern_id": str(updated_pattern.id),
                    "source_agent_type": updated_pattern.source_agent_type,
                    "target_agent_type": updated_pattern.target_agent_type,
                }
            )
            
            return updated_pattern
        except PatternNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating collaboration pattern: {str(e)}")
            raise DatabaseError(f"Failed to update collaboration pattern: {str(e)}")
    
    async def delete_pattern(
        self,
        pattern_id: UUID,
    ) -> None:
        """
        Delete a collaboration pattern.
        
        Args:
            pattern_id: Collaboration pattern ID
            
        Raises:
            PatternNotFoundError: If pattern not found
            DatabaseError: If database operation fails
        """
        try:
            # Begin transaction
            async with self.db.begin():
                # Check if pattern exists
                check_query = """
                SELECT 
                    source_agent_type,
                    target_agent_type
                FROM 
                    collaboration_pattern 
                WHERE 
                    id = :pattern_id
                """
                result = await self.db.execute(text(check_query), {"pattern_id": pattern_id})
                row = result.fetchone()
                
                if not row:
                    raise PatternNotFoundError(pattern_id)
                
                source_agent_type = row.source_agent_type
                target_agent_type = row.target_agent_type
                
                # Delete pattern
                delete_query = "DELETE FROM collaboration_pattern WHERE id = :pattern_id"
                await self.db.execute(text(delete_query), {"pattern_id": pattern_id})
            
            # Publish event
            await self.event_bus.publish_event(
                "agent.collaboration_pattern.deleted",
                {
                    "pattern_id": str(pattern_id),
                    "source_agent_type": source_agent_type,
                    "target_agent_type": target_agent_type,
                }
            )
        except PatternNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting collaboration pattern: {str(e)}")
            raise DatabaseError(f"Failed to delete collaboration pattern: {str(e)}")
    
    async def get_collaboration_graph(
        self,
        project_id: UUID,
    ) -> CollaborationGraph:
        """
        Get the collaboration graph for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            CollaborationGraph: Collaboration graph
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Query agents for the project
            agents_query = """
            SELECT 
                a.id,
                a.agent_type,
                a.name,
                a.metadata
            FROM 
                agent a
            WHERE 
                a.project_id = :project_id
            """
            
            # Execute query
            agents_result = await self.db.execute(
                text(agents_query),
                {"project_id": project_id},
            )
            
            # Get all rows
            agent_rows = agents_result.fetchall()
            
            # Create nodes
            nodes = []
            agent_ids_by_type = {}
            
            for row in agent_rows:
                agent_type = row.agent_type
                agent_id = row.id
                
                # Add to agent_ids_by_type
                if agent_type not in agent_ids_by_type:
                    agent_ids_by_type[agent_type] = []
                agent_ids_by_type[agent_type].append(agent_id)
                
                # Create node
                node = CollaborationGraphNode(
                    agent_type=agent_type,
                    agent_id=agent_id,
                    metadata={
                        "name": row.name,
                        "agent_metadata": row.metadata,
                    },
                )
                nodes.append(node)
            
            # Query patterns for the project
            patterns_query = """
            SELECT 
                p.id,
                p.source_agent_type,
                p.target_agent_type,
                p.interaction_type,
                p.description,
                p.priority,
                p.metadata
            FROM 
                collaboration_pattern p
            WHERE 
                (p.source_agent_type IN (SELECT DISTINCT agent_type FROM agent WHERE project_id = :project_id))
                OR (p.target_agent_type IN (SELECT DISTINCT agent_type FROM agent WHERE project_id = :project_id))
            """
            
            # Execute query
            patterns_result = await self.db.execute(
                text(patterns_query),
                {"project_id": project_id},
            )
            
            # Get all rows
            pattern_rows = patterns_result.fetchall()
            
            # Create edges
            edges = []
            edge_map = {}  # (source, target, interaction_type) -> edge
            
            for row in pattern_rows:
                source = row.source_agent_type
                target = row.target_agent_type
                interaction_type = row.interaction_type
                pattern_id = row.id
                
                # Create edge key
                edge_key = (source, target, interaction_type)
                
                # Add to edge map or update existing edge
                if edge_key in edge_map:
                    edge = edge_map[edge_key]
                    edge.patterns.append(pattern_id)
                else:
                    edge = CollaborationGraphEdge(
                        source=source,
                        target=target,
                        interaction_type=interaction_type,
                        patterns=[pattern_id],
                        metadata={
                            "description": row.description,
                            "priority": row.priority,
                            "pattern_metadata": row.metadata,
                        },
                    )
                    edge_map[edge_key] = edge
                    edges.append(edge)
            
            # Create graph
            graph = CollaborationGraph(
                project_id=project_id,
                nodes=nodes,
                edges=edges,
                metadata={
                    "created_at": str(await self._get_current_timestamp()),
                    "agent_count": len(nodes),
                    "pattern_count": len(pattern_rows),
                },
            )
            
            return graph
        except Exception as e:
            logger.error(f"Error getting collaboration graph: {str(e)}")
            raise DatabaseError(f"Failed to get collaboration graph: {str(e)}")
    
    async def _get_current_timestamp(self) -> str:
        """
        Get current timestamp from database.
        
        Returns:
            str: Current timestamp
        """
        result = await self.db.execute(text("SELECT now()"))
        return result.scalar_one()
    
    async def setup_project_communication_rules(
        self,
        project_id: UUID,
    ) -> Dict[str, Any]:
        """
        Setup communication rules for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Dict[str, Any]: Result of the operation
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Check if enhanced communication service is available
            if not self.enhanced_communication_service:
                return {
                    "success": False,
                    "message": "Enhanced communication service not available",
                }
            
            # Get collaboration graph
            graph = await self.get_collaboration_graph(project_id)
            
            # Create agent_ids map
            agent_ids = {}
            for node in graph.nodes:
                if node.agent_type not in agent_ids:
                    agent_ids[node.agent_type] = []
                agent_ids[node.agent_type].append(node.agent_id)
            
            # Create collaboration patterns map
            collaboration_patterns = {}
            for edge in graph.edges:
                if edge.source not in collaboration_patterns:
                    collaboration_patterns[edge.source] = []
                
                # Add pattern for each agent ID
                for pattern_id in edge.patterns:
                    pattern = {
                        "collaborator_type": edge.target,
                        "interaction_type": edge.interaction_type,
                        "description": edge.metadata.get("description", ""),
                    }
                    collaboration_patterns[edge.source].append(pattern)
            
            # Setup communication rules
            for agent_type, patterns in collaboration_patterns.items():
                # Skip if agent type not in agent_ids
                if agent_type not in agent_ids:
                    continue
                
                # Setup rules for each agent ID
                for agent_id in agent_ids[agent_type]:
                    # Create agent_ids map for this agent
                    agent_id_map = {}
                    for node_type, node_ids in agent_ids.items():
                        if node_ids:
                            agent_id_map[node_type] = node_ids[0]  # Use first agent ID for each type
                    
                    # Setup rules
                    await self.setup_communication_rules(
                        collaboration_patterns,
                        agent_id_map,
                        self.enhanced_communication_service,
                    )
            
            return {
                "success": True,
                "message": "Communication rules setup successfully",
                "agent_count": len(graph.nodes),
                "pattern_count": sum(len(patterns) for patterns in collaboration_patterns.values()),
            }
        except Exception as e:
            logger.error(f"Error setting up project communication rules: {str(e)}")
            raise DatabaseError(f"Failed to setup project communication rules: {str(e)}")
    
    async def identify_collaboration_patterns(
        self,
        agent_specializations: List[AgentSpecializationRequirement],
        requirements: List[RequirementItem],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Identify collaboration patterns between agents.
        
        Args:
            agent_specializations: List of agent specialization requirements
            requirements: List of requirements
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Collaboration patterns by agent type
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Initialize collaboration patterns
            collaboration_patterns = {}
            
            # Get collaboration patterns from agent specializations
            for specialization in agent_specializations:
                agent_type = specialization.agent_type.value
                collaboration_patterns[agent_type] = specialization.collaboration_patterns
            
            # Identify additional patterns from requirements
            additional_patterns = self._identify_patterns_from_requirements(requirements)
            
            # Merge additional patterns with existing patterns
            for agent_type, patterns in additional_patterns.items():
                if agent_type not in collaboration_patterns:
                    collaboration_patterns[agent_type] = []
                
                # Add new patterns if they don't already exist
                for pattern in patterns:
                    if not self._pattern_exists(pattern, collaboration_patterns[agent_type]):
                        collaboration_patterns[agent_type].append(pattern)
            
            # Ensure all agent types have at least an empty list
            for specialization in agent_specializations:
                agent_type = specialization.agent_type.value
                if agent_type not in collaboration_patterns:
                    collaboration_patterns[agent_type] = []
            
            return collaboration_patterns
        except Exception as e:
            logger.error(f"Error identifying collaboration patterns: {str(e)}")
            raise DatabaseError(f"Failed to identify collaboration patterns: {str(e)}")
    
    def _identify_patterns_from_requirements(
        self,
        requirements: List[RequirementItem],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Identify collaboration patterns from requirements.
        
        Args:
            requirements: List of requirements
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Collaboration patterns by agent type
        """
        collaboration_patterns = {}
        
        # Identify patterns from requirements with multiple agent types
        for req in requirements:
            if len(req.agent_types) > 1:
                for i, agent_type1 in enumerate(req.agent_types):
                    for agent_type2 in req.agent_types[i+1:]:
                        # Create patterns for both directions
                        self._add_pattern_from_requirement(
                            collaboration_patterns,
                            agent_type1.value,
                            agent_type2.value,
                            req,
                        )
                        
                        self._add_pattern_from_requirement(
                            collaboration_patterns,
                            agent_type2.value,
                            agent_type1.value,
                            req,
                        )
        
        return collaboration_patterns
    
    def _add_pattern_from_requirement(
        self,
        patterns: Dict[str, List[Dict[str, Any]]],
        from_agent_type: str,
        to_agent_type: str,
        requirement: RequirementItem,
    ) -> None:
        """
        Add a collaboration pattern from a requirement.
        
        Args:
            patterns: Collaboration patterns by agent type
            from_agent_type: Source agent type
            to_agent_type: Target agent type
            requirement: Requirement
        """
        # Initialize patterns for agent type if not exists
        if from_agent_type not in patterns:
            patterns[from_agent_type] = []
        
        # Determine interaction type based on requirement category
        interaction_type = self._determine_interaction_type(requirement)
        
        # Create pattern
        pattern = {
            "collaborator_type": to_agent_type,
            "interaction_type": interaction_type,
            "description": f"Collaborate on {requirement.description}",
        }
        
        # Add pattern if it doesn't already exist
        if not self._pattern_exists(pattern, patterns[from_agent_type]):
            patterns[from_agent_type].append(pattern)
    
    def _determine_interaction_type(self, requirement: RequirementItem) -> str:
        """
        Determine interaction type based on requirement.
        
        Args:
            requirement: Requirement
            
        Returns:
            str: Interaction type
        """
        # Map requirement categories to interaction types
        category_to_interaction = {
            "FUNCTIONAL": "IMPLEMENT_FEATURE",
            "NON_FUNCTIONAL": "ENSURE_QUALITY",
            "DOMAIN_SPECIFIC": "PROVIDE_DOMAIN_KNOWLEDGE",
            "TECHNICAL": "PROVIDE_TECHNICAL_EXPERTISE",
            "INTEGRATION": "COORDINATE_INTEGRATION",
            "COLLABORATION": "FACILITATE_COMMUNICATION",
        }
        
        # Get interaction type based on category
        interaction_type = category_to_interaction.get(requirement.category, "COLLABORATE")
        
        # Adjust based on priority
        if requirement.priority == "CRITICAL":
            interaction_type = "PRIORITIZE_" + interaction_type
        
        return interaction_type
    
    def _pattern_exists(self, pattern: Dict[str, Any], patterns: List[Dict[str, Any]]) -> bool:
        """
        Check if a pattern already exists in a list of patterns.
        
        Args:
            pattern: Pattern to check
            patterns: List of patterns
            
        Returns:
            bool: True if pattern exists, False otherwise
        """
        for existing_pattern in patterns:
            if (
                existing_pattern.get("collaborator_type") == pattern.get("collaborator_type") and
                existing_pattern.get("interaction_type") == pattern.get("interaction_type")
            ):
                return True
        return False
    
    async def generate_collaboration_graph(
        self,
        agent_specializations: List[AgentSpecializationRequirement],
        requirements: List[RequirementItem],
    ) -> Dict[str, List[str]]:
        """
        Generate collaboration graph between agent types.
        
        Args:
            agent_specializations: List of agent specialization requirements
            requirements: List of requirements
            
        Returns:
            Dict[str, List[str]]: Collaboration graph
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            collaboration_graph = {}
            
            # Initialize graph with agent types
            for specialization in agent_specializations:
                collaboration_graph[specialization.agent_type.value] = []
            
            # Add collaborations from specialization patterns
            for specialization in agent_specializations:
                for pattern in specialization.collaboration_patterns:
                    collaborator_type = pattern.get("collaborator_type")
                    if collaborator_type and collaborator_type in AgentType.__members__:
                        if collaborator_type not in collaboration_graph[specialization.agent_type.value]:
                            collaboration_graph[specialization.agent_type.value].append(collaborator_type)
            
            # Add collaborations from requirements
            for req in requirements:
                if len(req.agent_types) > 1:
                    for i, agent_type1 in enumerate(req.agent_types):
                        for agent_type2 in req.agent_types[i+1:]:
                            if agent_type2.value not in collaboration_graph.get(agent_type1.value, []):
                                if agent_type1.value not in collaboration_graph:
                                    collaboration_graph[agent_type1.value] = []
                                collaboration_graph[agent_type1.value].append(agent_type2.value)
                            
                            if agent_type1.value not in collaboration_graph.get(agent_type2.value, []):
                                if agent_type2.value not in collaboration_graph:
                                    collaboration_graph[agent_type2.value] = []
                                collaboration_graph[agent_type2.value].append(agent_type1.value)
            
            return collaboration_graph
        except Exception as e:
            logger.error(f"Error generating collaboration graph: {str(e)}")
            raise DatabaseError(f"Failed to generate collaboration graph: {str(e)}")
    
    async def setup_communication_rules(
        self,
        collaboration_patterns: Dict[str, List[Dict[str, Any]]],
        agent_ids: Dict[str, UUID],
        communication_service,
    ) -> None:
        """
        Set up communication rules based on collaboration patterns.
        
        Args:
            collaboration_patterns: Collaboration patterns by agent type
            agent_ids: Agent IDs by agent type
            communication_service: Communication service
            
        Raises:
            AgentNotFoundError: If agent not found
            DatabaseError: If database operation fails
        """
        try:
            # Set up rules for each agent type
            for agent_type, patterns in collaboration_patterns.items():
                # Skip if agent type not in agent_ids
                if agent_type not in agent_ids:
                    continue
                
                source_agent_id = agent_ids[agent_type]
                
                # Set up rules for each pattern
                for pattern in patterns:
                    collaborator_type = pattern.get("collaborator_type")
                    interaction_type = pattern.get("interaction_type")
                    
                    # Skip if collaborator type not in agent_ids
                    if collaborator_type not in agent_ids:
                        continue
                    
                    destination_agent_id = agent_ids[collaborator_type]
                    
                    # Set up rule based on interaction type
                    if interaction_type.startswith("PRIORITIZE_"):
                        # High priority rule
                        await self._setup_high_priority_rule(
                            source_agent_id,
                            destination_agent_id,
                            interaction_type,
                            communication_service,
                        )
                    elif interaction_type in ["IMPLEMENT_FEATURE", "ENSURE_QUALITY", "COORDINATE_INTEGRATION"]:
                        # Task-based rule
                        await self._setup_task_based_rule(
                            source_agent_id,
                            destination_agent_id,
                            interaction_type,
                            communication_service,
                        )
                    elif interaction_type in ["PROVIDE_DOMAIN_KNOWLEDGE", "PROVIDE_TECHNICAL_EXPERTISE"]:
                        # Knowledge-based rule
                        await self._setup_knowledge_based_rule(
                            source_agent_id,
                            destination_agent_id,
                            interaction_type,
                            communication_service,
                        )
                    else:
                        # Default rule
                        await self._setup_default_rule(
                            source_agent_id,
                            destination_agent_id,
                            interaction_type,
                            communication_service,
                        )
            
            logger.info("Communication rules set up successfully")
        except Exception as e:
            logger.error(f"Error setting up communication rules: {str(e)}")
            
            if isinstance(e, AgentNotFoundError):
                raise
            
            raise DatabaseError(f"Failed to set up communication rules: {str(e)}")
    
    async def _setup_high_priority_rule(
        self,
        source_agent_id: UUID,
        destination_agent_id: UUID,
        interaction_type: str,
        communication_service,
    ) -> None:
        """
        Set up a high priority rule.
        
        Args:
            source_agent_id: Source agent ID
            destination_agent_id: Destination agent ID
            interaction_type: Interaction type
            communication_service: Communication service
        """
        # Create a content-based rule for high priority messages
        async def high_priority_condition(message: Dict[str, Any]) -> bool:
            return (
                message.get("source_agent_id") == str(source_agent_id) and
                message.get("headers", {}).get("interaction_type") == interaction_type
            )
        
        # Add the rule
        await communication_service.add_content_rule(
            high_priority_condition,
            destination_agent_id,
        )
        
        # Set up a topic for this interaction
        topic = f"{interaction_type.lower()}_{source_agent_id}_{destination_agent_id}"
        
        # Subscribe the destination agent to the topic
        await communication_service.subscribe(
            str(destination_agent_id),
            topic,
        )
        
        logger.info(f"Set up high priority rule from {source_agent_id} to {destination_agent_id} for {interaction_type}")
    
    async def _setup_task_based_rule(
        self,
        source_agent_id: UUID,
        destination_agent_id: UUID,
        interaction_type: str,
        communication_service,
    ) -> None:
        """
        Set up a task-based rule.
        
        Args:
            source_agent_id: Source agent ID
            destination_agent_id: Destination agent ID
            interaction_type: Interaction type
            communication_service: Communication service
        """
        # Create a rule-based rule for task-based interactions
        rule = {
            "name": f"{interaction_type.lower()}_{source_agent_id}_{destination_agent_id}",
            "conditions": [
                {
                    "field": "source_agent_id",
                    "operator": "equals",
                    "value": str(source_agent_id),
                },
                {
                    "field": "headers.interaction_type",
                    "operator": "equals",
                    "value": interaction_type,
                },
                {
                    "field": "type",
                    "operator": "equals",
                    "value": "task",
                },
            ],
            "actions": [
                {
                    "type": "route",
                    "destination": {
                        "type": "agent",
                        "id": str(destination_agent_id),
                    },
                },
                {
                    "type": "set_priority",
                    "priority": 3,  # Medium-high priority
                },
            ],
        }
        
        # Add the rule
        await communication_service.add_rule(rule)
        
        logger.info(f"Set up task-based rule from {source_agent_id} to {destination_agent_id} for {interaction_type}")
    
    async def _setup_knowledge_based_rule(
        self,
        source_agent_id: UUID,
        destination_agent_id: UUID,
        interaction_type: str,
        communication_service,
    ) -> None:
        """
        Set up a knowledge-based rule.
        
        Args:
            source_agent_id: Source agent ID
            destination_agent_id: Destination agent ID
            interaction_type: Interaction type
            communication_service: Communication service
        """
        # Create a rule-based rule for knowledge-based interactions
        rule = {
            "name": f"{interaction_type.lower()}_{source_agent_id}_{destination_agent_id}",
            "conditions": [
                {
                    "field": "source_agent_id",
                    "operator": "equals",
                    "value": str(source_agent_id),
                },
                {
                    "field": "headers.interaction_type",
                    "operator": "equals",
                    "value": interaction_type,
                },
                {
                    "field": "type",
                    "operator": "equals",
                    "value": "knowledge_request",
                },
            ],
            "actions": [
                {
                    "type": "route",
                    "destination": {
                        "type": "agent",
                        "id": str(destination_agent_id),
                    },
                },
                {
                    "type": "set_priority",
                    "priority": 2,  # Medium priority
                },
            ],
        }
        
        # Add the rule
        await communication_service.add_rule(rule)
        
        logger.info(f"Set up knowledge-based rule from {source_agent_id} to {destination_agent_id} for {interaction_type}")
    
    async def _setup_default_rule(
        self,
        source_agent_id: UUID,
        destination_agent_id: UUID,
        interaction_type: str,
        communication_service,
    ) -> None:
        """
        Set up a default rule.
        
        Args:
            source_agent_id: Source agent ID
            destination_agent_id: Destination agent ID
            interaction_type: Interaction type
            communication_service: Communication service
        """
        # Create a rule-based rule for default interactions
        rule = {
            "name": f"{interaction_type.lower()}_{source_agent_id}_{destination_agent_id}",
            "conditions": [
                {
                    "field": "source_agent_id",
                    "operator": "equals",
                    "value": str(source_agent_id),
                },
                {
                    "field": "headers.interaction_type",
                    "operator": "equals",
                    "value": interaction_type,
                },
            ],
            "actions": [
                {
                    "type": "route",
                    "destination": {
                        "type": "agent",
                        "id": str(destination_agent_id),
                    },
                },
                {
                    "type": "set_priority",
                    "priority": 1,  # Normal priority
                },
            ],
        }
        
        # Add the rule
        await communication_service.add_rule(rule)
        
        logger.info(f"Set up default rule from {source_agent_id} to {destination_agent_id} for {interaction_type}")
