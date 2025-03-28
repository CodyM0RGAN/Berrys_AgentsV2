import logging
import json
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime

from shared.utils.src.messaging import EventBus, CommandBus

from ..config import AgentOrchestratorConfig
from ..exceptions import (
    TemplateNotFoundError,
    TemplateValidationError,
    DatabaseError,
)
from ..models.api import (
    AgentTemplateCreate,
    AgentTemplateUpdate,
    AgentTemplate,
    AgentType,
)
from ..models.internal import (
    AgentTemplateModel,
)

logger = logging.getLogger(__name__)


class TemplateService:
    """
    Service for agent template operations.
    """
    
    def __init__(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        command_bus: CommandBus,
        settings: AgentOrchestratorConfig,
    ):
        """
        Initialize the template service.
        
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
    
    async def create_template(self, template_data: AgentTemplateCreate) -> AgentTemplate:
        """
        Create a new agent template.
        
        Args:
            template_data: Template data
            
        Returns:
            AgentTemplate: Created template
            
        Raises:
            TemplateValidationError: If template data is invalid
            DatabaseError: If database operation fails
        """
        try:
            # Validate template data
            validation_errors = self._validate_template(template_data)
            if validation_errors:
                raise TemplateValidationError(
                    template_id=template_data.id or "new_template",
                    errors=validation_errors,
                )
            
            # Generate ID if not provided
            template_id = template_data.id or f"{template_data.agent_type.lower()}_template"
            
            # Check if template with ID already exists
            query = select(AgentTemplateModel).where(AgentTemplateModel.id == template_id)
            result = await self.db.execute(query)
            existing_template = result.scalars().first()
            
            if existing_template:
                raise TemplateValidationError(
                    template_id=template_id,
                    errors=["Template with this ID already exists"],
                )
            
            # Create template model
            template_model = AgentTemplateModel(
                id=template_id,
                name=template_data.name,
                description=template_data.description,
                agent_type=template_data.agent_type,
                configuration_schema=template_data.configuration_schema,
                default_configuration=template_data.default_configuration,
                prompt_template=template_data.prompt_template,
            )
            
            # Add to database
            self.db.add(template_model)
            await self.db.commit()
            await self.db.refresh(template_model)
            
            # Convert to API model
            template = AgentTemplate.from_orm(template_model)
            
            # Publish event
            await self.event_bus.publish_event(
                "agent.template.created",
                {
                    "template_id": template.id,
                    "name": template.name,
                    "agent_type": template.agent_type.value,
                }
            )
            
            return template
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating template: {str(e)}")
            
            if isinstance(e, TemplateValidationError):
                raise
            
            raise DatabaseError(f"Failed to create template: {str(e)}")
    
    async def get_template(self, template_id: str) -> Optional[AgentTemplate]:
        """
        Get a template by ID.
        
        Args:
            template_id: Template ID
            
        Returns:
            Optional[AgentTemplate]: Template if found, None otherwise
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Query template
            query = select(AgentTemplateModel).where(AgentTemplateModel.id == template_id)
            result = await self.db.execute(query)
            template_model = result.scalars().first()
            
            # Return None if not found
            if not template_model:
                return None
            
            # Convert to API model
            return AgentTemplate.from_orm(template_model)
        except Exception as e:
            logger.error(f"Error getting template {template_id}: {str(e)}")
            raise DatabaseError(f"Failed to get template: {str(e)}")
    
    async def list_templates(
        self,
        page: int = 1,
        page_size: int = 20,
        agent_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[AgentTemplate], int]:
        """
        List templates with pagination and filtering.
        
        Args:
            page: Page number
            page_size: Page size
            agent_type: Filter by agent type
            search: Search term
            
        Returns:
            Tuple[List[AgentTemplate], int]: List of templates and total count
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Build query
            query = select(AgentTemplateModel)
            count_query = select(func.count()).select_from(AgentTemplateModel)
            
            # Apply filters
            filters = []
            
            if agent_type:
                try:
                    agent_type_enum = AgentType(agent_type)
                    filters.append(AgentTemplateModel.agent_type == agent_type_enum)
                except ValueError:
                    # Invalid agent type, ignore filter
                    pass
            
            if search:
                search_filter = or_(
                    AgentTemplateModel.name.ilike(f"%{search}%"),
                    AgentTemplateModel.description.ilike(f"%{search}%"),
                )
                filters.append(search_filter)
            
            # Apply filters to queries
            if filters:
                filter_clause = and_(*filters)
                query = query.where(filter_clause)
                count_query = count_query.where(filter_clause)
            
            # Get total count
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()
            
            # Apply pagination
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            # Execute query
            result = await self.db.execute(query)
            template_models = result.scalars().all()
            
            # Convert to API models
            templates = [AgentTemplate.from_orm(model) for model in template_models]
            
            return templates, total
        except Exception as e:
            logger.error(f"Error listing templates: {str(e)}")
            raise DatabaseError(f"Failed to list templates: {str(e)}")
    
    async def update_template(
        self,
        template_id: str,
        template_update: AgentTemplateUpdate,
    ) -> AgentTemplate:
        """
        Update a template.
        
        Args:
            template_id: Template ID
            template_update: Template update data
            
        Returns:
            AgentTemplate: Updated template
            
        Raises:
            TemplateNotFoundError: If template not found
            TemplateValidationError: If template data is invalid
            DatabaseError: If database operation fails
        """
        try:
            # Query template
            query = select(AgentTemplateModel).where(AgentTemplateModel.id == template_id)
            result = await self.db.execute(query)
            template_model = result.scalars().first()
            
            # Check if template exists
            if not template_model:
                raise TemplateNotFoundError(template_id)
            
            # Update fields
            update_data = template_update.dict(exclude_unset=True)
            updated_fields = list(update_data.keys())
            
            for key, value in update_data.items():
                if key == "configuration_schema" and value is not None:
                    # Merge configuration schema
                    current_schema = template_model.configuration_schema or {}
                    current_schema.update(value)
                    setattr(template_model, key, current_schema)
                elif key == "default_configuration" and value is not None:
                    # Merge default configuration
                    current_config = template_model.default_configuration or {}
                    current_config.update(value)
                    setattr(template_model, key, current_config)
                else:
                    setattr(template_model, key, value)
            
            # Update timestamp
            template_model.updated_at = datetime.utcnow()
            
            # Commit changes
            await self.db.commit()
            await self.db.refresh(template_model)
            
            # Convert to API model
            template = AgentTemplate.from_orm(template_model)
            
            # Publish event
            await self.event_bus.publish_event(
                "agent.template.updated",
                {
                    "template_id": template.id,
                    "name": template.name,
                    "agent_type": template.agent_type.value,
                    "updated_fields": updated_fields,
                }
            )
            
            return template
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating template {template_id}: {str(e)}")
            
            if isinstance(e, (TemplateNotFoundError, TemplateValidationError)):
                raise
            
            raise DatabaseError(f"Failed to update template: {str(e)}")
    
    async def delete_template(self, template_id: str) -> None:
        """
        Delete a template.
        
        Args:
            template_id: Template ID
            
        Raises:
            TemplateNotFoundError: If template not found
            DatabaseError: If database operation fails
        """
        try:
            # Query template
            query = select(AgentTemplateModel).where(AgentTemplateModel.id == template_id)
            result = await self.db.execute(query)
            template_model = result.scalars().first()
            
            # Check if template exists
            if not template_model:
                raise TemplateNotFoundError(template_id)
            
            # Store template data for event
            template_data = {
                "template_id": template_model.id,
                "name": template_model.name,
                "agent_type": template_model.agent_type.value,
            }
            
            # Delete template
            await self.db.delete(template_model)
            await self.db.commit()
            
            # Publish event
            await self.event_bus.publish_event(
                "agent.template.deleted",
                template_data
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting template {template_id}: {str(e)}")
            
            if isinstance(e, TemplateNotFoundError):
                raise
            
            raise DatabaseError(f"Failed to delete template: {str(e)}")
    
    def _validate_template(self, template_data: AgentTemplateCreate) -> List[str]:
        """
        Validate template data.
        
        Args:
            template_data: Template data
            
        Returns:
            List[str]: List of validation errors, empty if valid
        """
        errors = []
        
        # Validate name
        if not template_data.name:
            errors.append("Name is required")
        
        # Validate configuration schema
        if template_data.configuration_schema:
            # Check if it's a valid JSON Schema
            if not isinstance(template_data.configuration_schema, dict):
                errors.append("Configuration schema must be a JSON object")
            elif "type" not in template_data.configuration_schema:
                errors.append("Configuration schema must have a 'type' property")
        
        # Validate default configuration against schema
        if template_data.configuration_schema and template_data.default_configuration:
            # Basic validation - in a real implementation, use a JSON Schema validator
            if template_data.configuration_schema.get("type") != "object":
                errors.append("Configuration schema must have type 'object'")
            
            # Check required properties
            required_props = template_data.configuration_schema.get("required", [])
            for prop in required_props:
                if prop not in template_data.default_configuration:
                    errors.append(f"Default configuration missing required property '{prop}'")
        
        return errors
