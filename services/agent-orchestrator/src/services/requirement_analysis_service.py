"""
Requirement analysis service.

This module contains the service for analyzing project requirements and
determining agent specializations.
"""

import logging
import re
import json
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional, Any, Tuple, Set
from uuid import UUID

from shared.utils.src.messaging import EventBus, CommandBus
from shared.models.src.enums import AgentType

from ..config import AgentOrchestratorConfig
from ..exceptions import (
    InvalidRequestError,
    DatabaseError,
)
from ..models.requirement_analysis import (
    RequirementAnalysisRequest,
    RequirementAnalysisResult,
    RequirementItem,
    AgentSpecializationRequirement,
    RequirementCategory,
    RequirementPriority,
)
from .agent_specialization_service import AgentSpecializationService
from .collaboration_pattern_service import CollaborationPatternService

logger = logging.getLogger(__name__)


class RequirementAnalysisService:
    """
    Service for requirement analysis operations.
    """
    
    def __init__(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        command_bus: CommandBus,
        settings: AgentOrchestratorConfig,
        model_service_client=None,  # Will be injected
        agent_specialization_service: Optional[AgentSpecializationService] = None,
        collaboration_pattern_service: Optional[CollaborationPatternService] = None,
    ):
        """
        Initialize the requirement analysis service.
        
        Args:
            db: Database session
            event_bus: Event bus
            command_bus: Command bus
            settings: Application settings
            model_service_client: Model service client for AI model access
            agent_specialization_service: Agent specialization service
            collaboration_pattern_service: Collaboration pattern service
        """
        self.db = db
        self.event_bus = event_bus
        self.command_bus = command_bus
        self.settings = settings
        self.model_service_client = model_service_client
        self.agent_specialization_service = agent_specialization_service or AgentSpecializationService(
            db=db,
            event_bus=event_bus,
            command_bus=command_bus,
            settings=settings,
        )
        self.collaboration_pattern_service = collaboration_pattern_service or CollaborationPatternService(
            db=db,
            event_bus=event_bus,
            command_bus=command_bus,
            settings=settings,
            agent_specialization_service=self.agent_specialization_service,
        )
    
    async def analyze_requirements(
        self,
        request: RequirementAnalysisRequest,
    ) -> RequirementAnalysisResult:
        """
        Analyze project requirements and determine agent specializations.
        
        Args:
            request: Requirement analysis request
            
        Returns:
            RequirementAnalysisResult: Analysis result
            
        Raises:
            InvalidRequestError: If request is invalid
            DatabaseError: If database operation fails
        """
        try:
            # Validate request
            if not request.description:
                raise InvalidRequestError("Project description is required")
            
            # Extract requirements
            requirements = await self._extract_requirements(request.description, request.context)
            
            # Categorize and prioritize requirements
            categorized_requirements = self._categorize_requirements(requirements)
            prioritized_requirements = self._prioritize_requirements(categorized_requirements)
            
            # Determine agent specializations
            agent_specializations = await self._determine_agent_specializations(
                prioritized_requirements,
                request.context,
            )
            
            # Generate collaboration graph
            collaboration_graph = await self._generate_collaboration_graph(
                agent_specializations,
                prioritized_requirements,
            )
            
            # Count requirements by category and priority
            requirement_categories = self._count_by_category(prioritized_requirements)
            requirement_priorities = self._count_by_priority(prioritized_requirements)
            
            # Create result
            result = RequirementAnalysisResult(
                project_id=request.project_id,
                requirements=prioritized_requirements,
                agent_specializations=agent_specializations,
                requirement_categories=requirement_categories,
                requirement_priorities=requirement_priorities,
                collaboration_graph=collaboration_graph,
            )
            
            # Publish event
            await self.event_bus.publish_event(
                "agent.requirement_analysis.completed",
                {
                    "project_id": str(request.project_id),
                    "requirement_count": len(prioritized_requirements),
                    "agent_specialization_count": len(agent_specializations),
                }
            )
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing requirements: {str(e)}")
            
            if isinstance(e, InvalidRequestError):
                raise
            
            raise DatabaseError(f"Failed to analyze requirements: {str(e)}")
    
    async def _extract_requirements(
        self,
        description: str,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Extract requirements from project description using AI model.
        
        Args:
            description: Project description
            context: Additional context
            
        Returns:
            List[Dict[str, Any]]: List of extracted requirements
        """
        # Use AI model to extract requirements
        if self.model_service_client:
            # Prepare prompt for requirement extraction
            prompt = self._create_requirement_extraction_prompt(description, context)
            
            # Call model service
            response = await self.model_service_client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are a requirements analysis expert."},
                    {"role": "user", "content": prompt},
                ],
                model_id="gpt-4",  # Use a capable model for this task
                temperature=0.2,  # Low temperature for more deterministic output
                response_format={"type": "json_object"},
            )
            
            # Parse response
            try:
                content = response.choices[0].message.content
                requirements_data = json.loads(content)
                return requirements_data.get("requirements", [])
            except (json.JSONDecodeError, AttributeError, KeyError) as e:
                logger.error(f"Error parsing model response: {str(e)}")
                # Fall back to rule-based extraction
                return self._rule_based_requirement_extraction(description)
        else:
            # Fall back to rule-based extraction if model service is not available
            return self._rule_based_requirement_extraction(description)
    
    def _create_requirement_extraction_prompt(
        self,
        description: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Create a prompt for requirement extraction.
        
        Args:
            description: Project description
            context: Additional context
            
        Returns:
            str: Prompt for requirement extraction
        """
        prompt = f"""
        Analyze the following project description and extract all requirements:
        
        PROJECT DESCRIPTION:
        {description}
        
        ADDITIONAL CONTEXT:
        {json.dumps(context, indent=2)}
        
        For each requirement:
        1. Assign a unique ID (e.g., REQ-001)
        2. Provide a clear, concise description
        3. Include any relevant details from the context
        
        Format your response as a JSON object with a "requirements" array containing objects with the following properties:
        - id: Unique identifier for the requirement
        - description: Clear description of the requirement
        - source: Where this requirement was derived from (e.g., "project_description", "context", "inference")
        - confidence: A number between 0 and 1 indicating your confidence in this requirement (1 being highest)
        
        Example:
        {{
          "requirements": [
            {{
              "id": "REQ-001",
              "description": "The system must provide real-time inventory updates",
              "source": "project_description",
              "confidence": 0.9
            }},
            ...
          ]
        }}
        """
        return prompt
    
    def _rule_based_requirement_extraction(
        self,
        description: str,
    ) -> List[Dict[str, Any]]:
        """
        Extract requirements using rule-based approach.
        
        Args:
            description: Project description
            
        Returns:
            List[Dict[str, Any]]: List of extracted requirements
        """
        requirements = []
        
        # Split description into sentences
        sentences = re.split(r'(?<=[.!?])\s+', description)
        
        # Keywords that often indicate requirements
        requirement_indicators = [
            "must", "should", "shall", "will", "needs to", "has to",
            "required", "necessary", "important", "critical", "essential",
            "feature", "functionality", "capability", "ability",
        ]
        
        req_id = 1
        for sentence in sentences:
            # Check if sentence contains requirement indicators
            if any(indicator in sentence.lower() for indicator in requirement_indicators):
                requirements.append({
                    "id": f"REQ-{req_id:03d}",
                    "description": sentence.strip(),
                    "source": "rule_based_extraction",
                    "confidence": 0.7,  # Medium confidence for rule-based extraction
                })
                req_id += 1
        
        return requirements
    
    def _categorize_requirements(
        self,
        requirements: List[Dict[str, Any]],
    ) -> List[RequirementItem]:
        """
        Categorize requirements.
        
        Args:
            requirements: List of extracted requirements
            
        Returns:
            List[RequirementItem]: List of categorized requirements
        """
        categorized_requirements = []
        
        # Category keywords
        category_keywords = {
            RequirementCategory.FUNCTIONAL: [
                "must", "should", "shall", "will", "perform", "function", "feature",
                "provide", "support", "enable", "allow", "process", "generate",
            ],
            RequirementCategory.NON_FUNCTIONAL: [
                "performance", "security", "reliability", "availability", "scalability",
                "usability", "maintainability", "portability", "efficiency", "fast",
                "secure", "reliable", "available", "scalable", "user-friendly",
            ],
            RequirementCategory.DOMAIN_SPECIFIC: [
                "business", "domain", "industry", "sector", "field", "area",
                "market", "customer", "client", "user", "stakeholder",
            ],
            RequirementCategory.TECHNICAL: [
                "technology", "technical", "architecture", "infrastructure", "platform",
                "framework", "library", "api", "interface", "protocol", "database",
                "storage", "memory", "cpu", "network", "cloud", "server", "client",
            ],
            RequirementCategory.INTEGRATION: [
                "integrate", "integration", "connect", "connection", "interface",
                "api", "service", "microservice", "system", "external", "third-party",
            ],
            RequirementCategory.COLLABORATION: [
                "collaborate", "collaboration", "team", "communication", "share",
                "sharing", "notification", "alert", "message", "chat", "email",
            ],
        }
        
        # Agent type keywords
        agent_type_keywords = {
            AgentType.COORDINATOR: [
                "coordinate", "coordination", "manage", "management", "oversee",
                "supervision", "planning", "plan", "schedule", "scheduling",
                "allocate", "allocation", "assign", "assignment",
            ],
            AgentType.ASSISTANT: [
                "assist", "assistance", "help", "support", "aid", "facilitate",
                "guidance", "guide", "advise", "advice", "suggestion", "suggest",
            ],
            AgentType.RESEARCHER: [
                "research", "analysis", "analyze", "investigate", "investigation",
                "explore", "exploration", "study", "examine", "examination",
                "data", "information", "knowledge", "insight", "discovery",
            ],
            AgentType.DEVELOPER: [
                "develop", "development", "code", "coding", "program", "programming",
                "implement", "implementation", "build", "construct", "create",
                "software", "application", "app", "system", "module", "component",
            ],
            AgentType.DESIGNER: [
                "design", "designing", "layout", "interface", "ui", "ux", "user interface",
                "user experience", "visual", "appearance", "look and feel", "aesthetic",
                "wireframe", "prototype", "mockup", "sketch", "graphic", "graphics",
            ],
            AgentType.SPECIALIST: [
                "specialist", "specialized", "specific", "domain", "expert", "expertise",
                "knowledge", "skill", "proficiency", "competence", "capability",
            ],
            AgentType.AUDITOR: [
                "audit", "auditing", "review", "reviewing", "verify", "verification",
                "validate", "validation", "check", "checking", "test", "testing",
                "quality", "assurance", "compliance", "standard", "regulation",
            ],
        }
        
        for req in requirements:
            description = req["description"].lower()
            
            # Determine category
            category = RequirementCategory.FUNCTIONAL  # Default category
            max_matches = 0
            
            for cat, keywords in category_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in description)
                if matches > max_matches:
                    max_matches = matches
                    category = cat
            
            # Determine agent types
            agent_types = []
            for agent_type, keywords in agent_type_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in description)
                if matches > 0:
                    agent_types.append(agent_type)
            
            # If no agent types matched, assign to DEVELOPER as default
            if not agent_types:
                agent_types = [AgentType.DEVELOPER]
            
            # Create requirement item
            requirement_item = RequirementItem(
                id=req["id"],
                description=req["description"],
                category=category,
                priority=RequirementPriority.MEDIUM,  # Default priority, will be updated later
                agent_types=agent_types,
                metadata={
                    "source": req.get("source", "unknown"),
                    "confidence": req.get("confidence", 0.5),
                },
            )
            
            categorized_requirements.append(requirement_item)
        
        return categorized_requirements
    
    def _prioritize_requirements(
        self,
        requirements: List[RequirementItem],
    ) -> List[RequirementItem]:
        """
        Prioritize requirements.
        
        Args:
            requirements: List of categorized requirements
            
        Returns:
            List[RequirementItem]: List of prioritized requirements
        """
        # Priority keywords
        priority_keywords = {
            RequirementPriority.CRITICAL: [
                "critical", "crucial", "essential", "vital", "must", "shall",
                "required", "necessary", "mandatory", "highest", "top", "key",
            ],
            RequirementPriority.HIGH: [
                "high", "important", "significant", "major", "primary", "should",
                "needed", "valuable", "substantial", "considerable",
            ],
            RequirementPriority.MEDIUM: [
                "medium", "moderate", "average", "standard", "normal", "regular",
                "intermediate", "middle", "mid-level", "secondary",
            ],
            RequirementPriority.LOW: [
                "low", "minor", "minimal", "small", "slight", "marginal",
                "optional", "nice-to-have", "desirable", "tertiary",
            ],
        }
        
        prioritized_requirements = []
        
        for req in requirements:
            description = req.description.lower()
            
            # Determine priority
            priority = RequirementPriority.MEDIUM  # Default priority
            max_matches = 0
            
            for pri, keywords in priority_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in description)
                if matches > max_matches:
                    max_matches = matches
                    priority = pri
            
            # Update priority
            req.priority = priority
            prioritized_requirements.append(req)
        
        return prioritized_requirements
    
    async def _determine_agent_specializations(
        self,
        requirements: List[RequirementItem],
        context: Dict[str, Any],
    ) -> List[AgentSpecializationRequirement]:
        """
        Determine agent specializations based on requirements.
        
        Args:
            requirements: List of prioritized requirements
            context: Additional context
            
        Returns:
            List[AgentSpecializationRequirement]: List of agent specialization requirements
        """
        # Group requirements by agent type
        agent_type_requirements = {}
        for req in requirements:
            for agent_type in req.agent_types:
                if agent_type not in agent_type_requirements:
                    agent_type_requirements[agent_type] = []
                agent_type_requirements[agent_type].append(req)
        
        # Determine specializations for each agent type
        specializations = []
        
        for agent_type, reqs in agent_type_requirements.items():
            # Use AI model to determine specialization if available
            if self.model_service_client:
                specialization = await self._ai_determine_specialization(agent_type, reqs, context)
                specializations.append(specialization)
            else:
                # Fall back to rule-based approach
                specialization = self._rule_based_determine_specialization(agent_type, reqs, context)
                specializations.append(specialization)
        
        return specializations
    
    async def _ai_determine_specialization(
        self,
        agent_type: AgentType,
        requirements: List[RequirementItem],
        context: Dict[str, Any],
    ) -> AgentSpecializationRequirement:
        """
        Determine agent specialization using AI model.
        
        Args:
            agent_type: Agent type
            requirements: List of requirements for this agent type
            context: Additional context
            
        Returns:
            AgentSpecializationRequirement: Agent specialization requirement
        """
        # Prepare prompt for specialization determination
        prompt = self._create_specialization_prompt(agent_type, requirements, context)
        
        # Call model service
        response = await self.model_service_client.chat_completion(
            messages=[
                {"role": "system", "content": "You are an agent specialization expert."},
                {"role": "user", "content": prompt},
            ],
            model_id="gpt-4",  # Use a capable model for this task
            temperature=0.2,  # Low temperature for more deterministic output
            response_format={"type": "json_object"},
        )
        
        # Parse response
        try:
            content = response.choices[0].message.content
            specialization_data = json.loads(content)
            
            return AgentSpecializationRequirement(
                agent_type=agent_type,
                required_skills=specialization_data.get("required_skills", []),
                responsibilities=specialization_data.get("responsibilities", []),
                knowledge_domains=specialization_data.get("knowledge_domains", []),
                collaboration_patterns=specialization_data.get("collaboration_patterns", []),
            )
        except (json.JSONDecodeError, AttributeError, KeyError) as e:
            logger.error(f"Error parsing model response: {str(e)}")
            # Fall back to rule-based approach
            return self._rule_based_determine_specialization(agent_type, requirements, context)
    
    def _create_specialization_prompt(
        self,
        agent_type: AgentType,
        requirements: List[RequirementItem],
        context: Dict[str, Any],
    ) -> str:
        """
        Create a prompt for specialization determination.
        
        Args:
            agent_type: Agent type
            requirements: List of requirements for this agent type
            context: Additional context
            
        Returns:
            str: Prompt for specialization determination
        """
        # Format requirements as text
        requirements_text = "\n".join([
            f"- {req.id}: {req.description} (Category: {req.category}, Priority: {req.priority})"
            for req in requirements
        ])
        
        prompt = f"""
        Determine the specialization requirements for a {agent_type.value} agent based on the following requirements:
        
        REQUIREMENTS:
        {requirements_text}
        
        ADDITIONAL CONTEXT:
        {json.dumps(context, indent=2)}
        
        For this {agent_type.value} agent, determine:
        1. Required skills
        2. Responsibilities
        3. Knowledge domains
        4. Collaboration patterns with other agent types
        
        Format your response as a JSON object with the following properties:
        - required_skills: Array of strings representing skills the agent needs
        - responsibilities: Array of strings representing the agent's responsibilities
        - knowledge_domains: Array of strings representing domains the agent needs knowledge in
        - collaboration_patterns: Array of objects with properties:
          - collaborator_type: The type of agent to collaborate with
          - interaction_type: The type of interaction (e.g., REQUEST_REVIEW, PROVIDE_INPUT)
          - description: Description of the collaboration
        
        Example:
        {{
          "required_skills": ["Web Development", "Database Design", "API Integration"],
          "responsibilities": ["Implement inventory tracking features", "Create database schema"],
          "knowledge_domains": ["Inventory Management", "Web Technologies"],
          "collaboration_patterns": [
            {{
              "collaborator_type": "DESIGNER",
              "interaction_type": "REQUEST_REVIEW",
              "description": "Request UI design review"
            }}
          ]
        }}
        """
        return prompt
    
    async def _rule_based_determine_specialization(
        self,
        agent_type: AgentType,
        requirements: List[RequirementItem],
        context: Dict[str, Any],
    ) -> AgentSpecializationRequirement:
        """
        Determine agent specialization using rule-based approach.
        
        Args:
            agent_type: Agent type
            requirements: List of requirements for this agent type
            context: Additional context
            
        Returns:
            AgentSpecializationRequirement: Agent specialization requirement
        """
        try:
            # Try to get specialization from database
            specialization = await self.agent_specialization_service.get_agent_specialization(agent_type)
            
            # If specialization found, return it
            if specialization:
                return specialization
            
            # If specialization not found, create a default one
            logger.warning(f"Specialization for agent type {agent_type} not found in database, using default")
            
            # Default specialization for unknown agent types
            default_specialization = AgentSpecializationRequirement(
                agent_type=agent_type,
                required_skills=["Adaptability", "Versatility", "Specialized Knowledge"],
                responsibilities=["Perform custom tasks", "Adapt to project needs"],
                knowledge_domains=["Project-Specific Domain"],
                collaboration_patterns=[
                    {
                        "collaborator_type": "COORDINATOR",
                        "interaction_type": "RECEIVE_INSTRUCTIONS",
                        "description": "Receive custom instructions"
                    }
                ],
            )
            
            return default_specialization
        except Exception as e:
            logger.error(f"Error determining specialization for agent type {agent_type}: {str(e)}")
            
            # Fallback to a minimal default specialization
            return AgentSpecializationRequirement(
                agent_type=agent_type,
                required_skills=["Adaptability"],
                responsibilities=["Perform tasks"],
                knowledge_domains=["General"],
                collaboration_patterns=[],
            )
    
    async def _generate_collaboration_graph(
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
        """
        try:
            # Use the collaboration pattern service to generate the graph
            return await self.collaboration_pattern_service.generate_collaboration_graph(
                agent_specializations,
                requirements,
            )
        except Exception as e:
            logger.error(f"Error generating collaboration graph: {str(e)}")
            
            # Fall back to simple graph generation
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
            
            return collaboration_graph
    
    def _count_by_category(
        self,
        requirements: List[RequirementItem],
    ) -> Dict[str, int]:
        """
        Count requirements by category.
        
        Args:
            requirements: List of requirements
            
        Returns:
            Dict[str, int]: Count of requirements by category
        """
        category_counts = {}
        
        for req in requirements:
            if req.category not in category_counts:
                category_counts[req.category] = 0
            category_counts[req.category] += 1
        
        return category_counts
    
    def _count_by_priority(
        self,
        requirements: List[RequirementItem],
    ) -> Dict[str, int]:
        """
        Count requirements by priority.
        
        Args:
            requirements: List of requirements
            
        Returns:
            Dict[str, int]: Count of requirements by priority
        """
        priority_counts = {}
        
        for req in requirements:
            if req.priority not in priority_counts:
                priority_counts[req.priority] = 0
            priority_counts[req.priority] += 1
        
        return priority_counts
