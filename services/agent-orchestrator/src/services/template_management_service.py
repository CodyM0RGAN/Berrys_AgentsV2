"""
Template Management Service.

This module provides the service layer for the Agent Template Engine.
"""

import logging
import hashlib
import json
import os
from typing import List, Dict, Optional, Any, Tuple, Union
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, update, delete, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from ..models.template_engine import (
    TemplateType,
    AgentTemplate as TemplateEngine,
    AgentTemplateCreate as TemplateEngineCreate,
    AgentTemplateUpdate as TemplateEngineUpdate,
    AgentTemplateVersion,
    TemplateTag,
    TemplateTagCreate,
    TemplateTagUpdate,
    TemplateAnalytics,
    TemplateCustomization,
    TemplateImportSource,
    VersionComparisonResult,
)
from ..models.template_engine_model import (
    AgentTemplateEngineModel,
    AgentTemplateVersionModel,
    TemplateTagModel,
    TemplateTagMappingModel,
    TemplateAnalyticsModel,
)
from ..exceptions import (
    NotFoundException,
    AlreadyExistsException,
    ValidationException,
    ServiceException,
)

logger = logging.getLogger(__name__)


class TemplateManagementService:
    """
    Service for managing agent templates.
    """
    
    def __init__(self, db_pool):
        """
        Initialize the service.
        
        Args:
            db_pool: Database connection pool
        """
        self.db_pool = db_pool
    
    async def get_template(self, session: AsyncSession, template_id: UUID) -> TemplateEngine:
        """
        Get a template by ID.
        
        Args:
            session: Database session
            template_id: Template ID
            
        Returns:
            TemplateEngine: Template
            
        Raises:
            NotFoundException: If template not found
        """
        query = select(AgentTemplateEngineModel).where(AgentTemplateEngineModel.id == template_id)
        result = await session.execute(query)
        template_model = result.scalars().first()
        
        if not template_model:
            raise NotFoundException(f"Template with ID {template_id} not found")
        
        return self._model_to_schema(template_model)
    
    async def list_templates(
        self,
        session: AsyncSession,
        agent_type: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search_term: Optional[str] = None,
        is_system_template: Optional[bool] = None,
        is_public: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[TemplateEngine], int]:
        """
        List templates with filtering options.
        
        Args:
            session: Database session
            agent_type: Filter by agent type
            category: Filter by category
            tags: Filter by tags
            search_term: Search term for name and description
            is_system_template: Filter by system template flag
            is_public: Filter by public flag
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple[List[TemplateEngine], int]: List of templates and total count
        """
        # Build query
        query = select(AgentTemplateEngineModel)
        count_query = select(func.count()).select_from(AgentTemplateEngineModel)
        
        # Apply filters
        if agent_type:
            query = query.where(AgentTemplateEngineModel.base_agent_type == agent_type)
            count_query = count_query.where(AgentTemplateEngineModel.base_agent_type == agent_type)
        
        if category:
            query = query.where(AgentTemplateEngineModel.category == category)
            count_query = count_query.where(AgentTemplateEngineModel.category == category)
        
        if is_system_template is not None:
            query = query.where(AgentTemplateEngineModel.is_system_template == is_system_template)
            count_query = count_query.where(AgentTemplateEngineModel.is_system_template == is_system_template)
        
        if is_public is not None:
            query = query.where(AgentTemplateEngineModel.is_public == is_public)
            count_query = count_query.where(AgentTemplateEngineModel.is_public == is_public)
        
        if search_term:
            search_filter = or_(
                AgentTemplateEngineModel.name.ilike(f"%{search_term}%"),
                AgentTemplateEngineModel.description.ilike(f"%{search_term}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Apply tag filtering if needed
        if tags:
            # Subquery to get template IDs with all the specified tags
            tag_subquery = (
                select(TemplateTagMappingModel.template_id)
                .join(TemplateTagModel, TemplateTagMappingModel.tag_id == TemplateTagModel.id)
                .where(TemplateTagModel.name.in_(tags))
                .group_by(TemplateTagMappingModel.template_id)
                .having(func.count(TemplateTagMappingModel.tag_id) == len(tags))
            )
            
            query = query.where(AgentTemplateEngineModel.id.in_(tag_subquery))
            count_query = count_query.where(AgentTemplateEngineModel.id.in_(tag_subquery))
        
        # Get total count
        count_result = await session.execute(count_query)
        total_count = count_result.scalar()
        
        # Apply pagination
        query = query.order_by(AgentTemplateEngineModel.name).offset(skip).limit(limit)
        
        # Execute query
        result = await session.execute(query)
        template_models = result.scalars().all()
        
        # Convert to schemas
        templates = [self._model_to_schema(model) for model in template_models]
        
        return templates, total_count
    
    async def create_template(
        self,
        session: AsyncSession,
        template: TemplateEngineCreate
    ) -> TemplateEngine:
        """
        Create a new template.
        
        Args:
            session: Database session
            template: Template to create
            
        Returns:
            TemplateEngine: Created template
            
        Raises:
            AlreadyExistsException: If template with same name and agent type already exists
            ValidationException: If template data is invalid
        """
        # Validate template data
        if not template.name or not template.template_type or not template.base_agent_type:
            raise ValidationException("Name, template type, and base agent type are required")
        
        # Create model
        template_model = AgentTemplateEngineModel(
            name=template.name,
            description=template.description,
            template_type=template.template_type,
            base_agent_type=template.base_agent_type,
            template_content=template.template_content,
            category=template.category,
            is_system_template=template.is_system_template,
            is_public=template.is_public,
            owner_id=template.owner_id,
        )
        
        # Generate checksum
        template_model.update_checksum()
        
        try:
            # Add to session
            session.add(template_model)
            await session.flush()
            
            # Create analytics record
            analytics_model = TemplateAnalyticsModel(
                template_id=template_model.id,
                usage_count=0,
            )
            session.add(analytics_model)
            
            # Create initial version
            version_model = AgentTemplateVersionModel(
                template_id=template_model.id,
                version_number=1,
                template_content=template.template_content,
                changelog="Initial version",
                created_by=template.owner_id,
            )
            session.add(version_model)
            
            await session.commit()
            
            return self._model_to_schema(template_model)
        except IntegrityError as e:
            await session.rollback()
            if "uq_template_name_agent_type" in str(e):
                raise AlreadyExistsException(f"Template with name '{template.name}' and agent type '{template.base_agent_type}' already exists")
            raise
    
    async def update_template(
        self,
        session: AsyncSession,
        template_id: UUID,
        template: TemplateEngineUpdate
    ) -> TemplateEngine:
        """
        Update a template.
        
        Args:
            session: Database session
            template_id: Template ID
            template: Template data to update
            
        Returns:
            TemplateEngine: Updated template
            
        Raises:
            NotFoundException: If template not found
            AlreadyExistsException: If template with same name and agent type already exists
        """
        # Get template
        query = select(AgentTemplateEngineModel).where(AgentTemplateEngineModel.id == template_id)
        result = await session.execute(query)
        template_model = result.scalars().first()
        
        if not template_model:
            raise NotFoundException(f"Template with ID {template_id} not found")
        
        # Check if template content is being updated
        content_updated = template.template_content is not None and template.template_content != template_model.template_content
        
        # Update fields
        if template.name is not None:
            template_model.name = template.name
        if template.description is not None:
            template_model.description = template.description
        if template.template_content is not None:
            template_model.template_content = template.template_content
        if template.category is not None:
            template_model.category = template.category
        if template.is_public is not None:
            template_model.is_public = template.is_public
        
        # Update checksum if content changed
        if content_updated:
            template_model.update_checksum()
        
        try:
            # Create new version if content changed
            if content_updated:
                # Get current max version number
                version_query = select(func.max(AgentTemplateVersionModel.version_number)).where(
                    AgentTemplateVersionModel.template_id == template_id
                )
                version_result = await session.execute(version_query)
                current_version = version_result.scalar() or 0
                
                # Create new version
                version_model = AgentTemplateVersionModel(
                    template_id=template_id,
                    version_number=current_version + 1,
                    template_content=template.template_content,
                    changelog="Updated template content",
                    created_by=None,  # Could be passed in the update request
                )
                session.add(version_model)
            
            await session.commit()
            
            return self._model_to_schema(template_model)
        except IntegrityError as e:
            await session.rollback()
            if "uq_template_name_agent_type" in str(e):
                raise AlreadyExistsException(f"Template with name '{template.name}' and agent type '{template_model.base_agent_type}' already exists")
            raise
    
    async def delete_template(self, session: AsyncSession, template_id: UUID) -> bool:
        """
        Delete a template.
        
        Args:
            session: Database session
            template_id: Template ID
            
        Returns:
            bool: True if deleted, False otherwise
            
        Raises:
            NotFoundException: If template not found
        """
        # Check if template exists
        query = select(AgentTemplateEngineModel).where(AgentTemplateEngineModel.id == template_id)
        result = await session.execute(query)
        template_model = result.scalars().first()
        
        if not template_model:
            raise NotFoundException(f"Template with ID {template_id} not found")
        
        # Delete template
        delete_query = delete(AgentTemplateEngineModel).where(AgentTemplateEngineModel.id == template_id)
        await session.execute(delete_query)
        await session.commit()
        
        return True
    
    async def get_template_versions(
        self,
        session: AsyncSession,
        template_id: UUID
    ) -> List[AgentTemplateVersion]:
        """
        Get all versions of a template.
        
        Args:
            session: Database session
            template_id: Template ID
            
        Returns:
            List[AgentTemplateVersion]: List of template versions
            
        Raises:
            NotFoundException: If template not found
        """
        # Check if template exists
        template_query = select(AgentTemplateEngineModel).where(AgentTemplateEngineModel.id == template_id)
        template_result = await session.execute(template_query)
        template_model = template_result.scalars().first()
        
        if not template_model:
            raise NotFoundException(f"Template with ID {template_id} not found")
        
        # Get versions
        query = select(AgentTemplateVersionModel).where(
            AgentTemplateVersionModel.template_id == template_id
        ).order_by(AgentTemplateVersionModel.version_number.desc())
        
        result = await session.execute(query)
        version_models = result.scalars().all()
        
        # Convert to schemas
        versions = [self._version_model_to_schema(model) for model in version_models]
        
        return versions
    
    async def get_template_version(
        self,
        session: AsyncSession,
        template_id: UUID,
        version_number: int
    ) -> AgentTemplateVersion:
        """
        Get a specific version of a template.
        
        Args:
            session: Database session
            template_id: Template ID
            version_number: Version number
            
        Returns:
            AgentTemplateVersion: Template version
            
        Raises:
            NotFoundException: If template or version not found
        """
        # Check if template exists
        template_query = select(AgentTemplateEngineModel).where(AgentTemplateEngineModel.id == template_id)
        template_result = await session.execute(template_query)
        template_model = template_result.scalars().first()
        
        if not template_model:
            raise NotFoundException(f"Template with ID {template_id} not found")
        
        # Get version
        query = select(AgentTemplateVersionModel).where(
            AgentTemplateVersionModel.template_id == template_id,
            AgentTemplateVersionModel.version_number == version_number
        )
        
        result = await session.execute(query)
        version_model = result.scalars().first()
        
        if not version_model:
            raise NotFoundException(f"Version {version_number} of template {template_id} not found")
        
        return self._version_model_to_schema(version_model)
    
    async def create_version(
        self,
        session: AsyncSession,
        template_id: UUID,
        changelog: str,
        creator_id: Optional[UUID] = None
    ) -> AgentTemplateVersion:
        """
        Manually create a new version of a template.
        
        Args:
            session: Database session
            template_id: Template ID
            changelog: Changelog message
            creator_id: Creator ID
            
        Returns:
            AgentTemplateVersion: Created version
            
        Raises:
            NotFoundException: If template not found
        """
        # Get template
        query = select(AgentTemplateEngineModel).where(AgentTemplateEngineModel.id == template_id)
        result = await session.execute(query)
        template_model = result.scalars().first()
        
        if not template_model:
            raise NotFoundException(f"Template with ID {template_id} not found")
        
        # Get current max version number
        version_query = select(func.max(AgentTemplateVersionModel.version_number)).where(
            AgentTemplateVersionModel.template_id == template_id
        )
        version_result = await session.execute(version_query)
        current_version = version_result.scalar() or 0
        
        # Create new version
        version_model = AgentTemplateVersionModel(
            template_id=template_id,
            version_number=current_version + 1,
            template_content=template_model.template_content,
            changelog=changelog,
            created_by=creator_id,
        )
        
        session.add(version_model)
        await session.commit()
        
        return self._version_model_to_schema(version_model)
    
    async def revert_to_version(
        self,
        session: AsyncSession,
        template_id: UUID,
        version_number: int
    ) -> TemplateEngine:
        """
        Revert a template to a previous version.
        
        Args:
            session: Database session
            template_id: Template ID
            version_number: Version number
            
        Returns:
            TemplateEngine: Updated template
            
        Raises:
            NotFoundException: If template or version not found
        """
        # Get template
        template_query = select(AgentTemplateEngineModel).where(AgentTemplateEngineModel.id == template_id)
        template_result = await session.execute(template_query)
        template_model = template_result.scalars().first()
        
        if not template_model:
            raise NotFoundException(f"Template with ID {template_id} not found")
        
        # Get version
        version_query = select(AgentTemplateVersionModel).where(
            AgentTemplateVersionModel.template_id == template_id,
            AgentTemplateVersionModel.version_number == version_number
        )
        version_result = await session.execute(version_query)
        version_model = version_result.scalars().first()
        
        if not version_model:
            raise NotFoundException(f"Version {version_number} of template {template_id} not found")
        
        # Update template content
        template_model.template_content = version_model.template_content
        template_model.update_checksum()
        
        # Get current max version number
        max_version_query = select(func.max(AgentTemplateVersionModel.version_number)).where(
            AgentTemplateVersionModel.template_id == template_id
        )
        max_version_result = await session.execute(max_version_query)
        current_version = max_version_result.scalar() or 0
        
        # Create new version
        new_version_model = AgentTemplateVersionModel(
            template_id=template_id,
            version_number=current_version + 1,
            template_content=version_model.template_content,
            changelog=f"Reverted to version {version_number}",
            created_by=None,
        )
        
        session.add(new_version_model)
        await session.commit()
        
        return self._model_to_schema(template_model)
    
    async def compare_versions(
        self,
        session: AsyncSession,
        template_id: UUID,
        version1: int,
        version2: int
    ) -> VersionComparisonResult:
        """
        Compare two versions of a template.
        
        Args:
            session: Database session
            template_id: Template ID
            version1: First version number
            version2: Second version number
            
        Returns:
            VersionComparisonResult: Comparison result
            
        Raises:
            NotFoundException: If template or versions not found
        """
        # Get template
        template_query = select(AgentTemplateEngineModel).where(AgentTemplateEngineModel.id == template_id)
        template_result = await session.execute(template_query)
        template_model = template_result.scalars().first()
        
        if not template_model:
            raise NotFoundException(f"Template with ID {template_id} not found")
        
        # Get versions
        version1_query = select(AgentTemplateVersionModel).where(
            AgentTemplateVersionModel.template_id == template_id,
            AgentTemplateVersionModel.version_number == version1
        )
        version1_result = await session.execute(version1_query)
        version1_model = version1_result.scalars().first()
        
        if not version1_model:
            raise NotFoundException(f"Version {version1} of template {template_id} not found")
        
        version2_query = select(AgentTemplateVersionModel).where(
            AgentTemplateVersionModel.template_id == template_id,
            AgentTemplateVersionModel.version_number == version2
        )
        version2_result = await session.execute(version2_query)
        version2_model = version2_result.scalars().first()
        
        if not version2_model:
            raise NotFoundException(f"Version {version2} of template {template_id} not found")
        
        # Compare versions
        differences = self._compare_json_objects(
            version1_model.template_content,
            version2_model.template_content
        )
        
        return VersionComparisonResult(
            template_id=template_id,
            version1=version1,
            version2=version2,
            differences=differences
        )
    
    async def list_tags(self, session: AsyncSession) -> List[TemplateTag]:
        """
        List all template tags.
        
        Args:
            session: Database session
            
        Returns:
            List[TemplateTag]: List of tags
        """
        query = select(TemplateTagModel).order_by(TemplateTagModel.name)
        result = await session.execute(query)
        tag_models = result.scalars().all()
        
        return [self._tag_model_to_schema(model) for model in tag_models]
    
    async def create_tag(self, session: AsyncSession, tag: TemplateTagCreate) -> TemplateTag:
        """
        Create a new tag.
        
        Args:
            session: Database session
            tag: Tag to create
            
        Returns:
            TemplateTag: Created tag
            
        Raises:
            AlreadyExistsException: If tag with same name already exists
        """
        # Create model
        tag_model = TemplateTagModel(
            name=tag.name,
            description=tag.description,
        )
        
        try:
            session.add(tag_model)
            await session.commit()
            
            return self._tag_model_to_schema(tag_model)
        except IntegrityError:
            await session.rollback()
            raise AlreadyExistsException(f"Tag with name '{tag.name}' already exists")
    
    async def update_tag(
        self,
        session: AsyncSession,
        tag_id: UUID,
        tag: TemplateTagUpdate
    ) -> TemplateTag:
        """
        Update a tag.
        
        Args:
            session: Database session
            tag_id: Tag ID
            tag: Tag data to update
            
        Returns:
            TemplateTag: Updated tag
            
        Raises:
            NotFoundException: If tag not found
            AlreadyExistsException: If tag with same name already exists
        """
        # Get tag
        query = select(TemplateTagModel).where(TemplateTagModel.id == tag_id)
        result = await session.execute(query)
        tag_model = result.scalars().first()
        
        if not tag_model:
            raise NotFoundException(f"Tag with ID {tag_id} not found")
        
        # Update fields
        if tag.name is not None:
            tag_model.name = tag.name
        if tag.description is not None:
            tag_model.description = tag.description
        
        try:
            await session.commit()
            
            return self._tag_model_to_schema(tag_model)
        except IntegrityError:
            await session.rollback()
            raise AlreadyExistsException(f"Tag with name '{tag.name}' already exists")
    
    async def delete_tag(self, session: AsyncSession, tag_id: UUID) -> bool:
        """
        Delete a tag.
        
        Args:
            session: Database session
            tag_id: Tag ID
            
        Returns:
            bool: True if deleted, False otherwise
            
        Raises:
            NotFoundException: If tag not found
        """
        # Check if tag exists
        query = select(TemplateTagModel).where(TemplateTagModel.id == tag_id)
        result = await session.execute(query)
        tag_model = result.scalars().first()
        
        if not tag_model:
            raise NotFoundException(f"Tag with ID {tag_id} not found")
        
        # Delete tag
        delete_query = delete(TemplateTagModel).where(TemplateTagModel.id == tag_id)
        await session.execute(delete_query)
        await session.commit()
        
        return True
    
    async def add_tag_to_template(
        self,
        session: AsyncSession,
        template_id: UUID,
        tag_id: UUID
    ) -> bool:
        """
        Add a tag to a template.
        
        Args:
            session: Database session
            template_id: Template ID
            tag_id: Tag ID
            
        Returns:
            bool: True if added, False otherwise
            
        Raises:
            NotFoundException: If template or tag not found
            AlreadyExistsException: If tag already added to template
        """
        # Check if template exists
        template_query = select(AgentTemplateEngineModel).where(AgentTemplateEngineModel.id == template_id)
        template_result = await session.execute(template_query)
        template_model = template_result.scalars().first()
        
        if not template_model:
            raise NotFoundException(f"Template with ID {template_id} not found")
        
        # Check if tag exists
        tag_query = select(TemplateTagModel).where(TemplateTagModel.id == tag_id)
        tag_result = await session.execute(tag_query)
        tag_model = tag_result.scalars().first()
        
        if not tag_model:
            raise NotFoundException(f"Tag with ID {tag_id} not found")
        
        # Check if mapping already exists
        mapping_query = select(TemplateTagMappingModel).where(
            TemplateTagMappingModel.template_id == template_id,
            TemplateTagMappingModel.tag_id == tag_id
        )
        mapping_result = await session.execute(mapping_query)
        mapping_model = mapping_result.scalars().first()
        
        if mapping_model:
            raise AlreadyExistsException(f"Tag {tag_id} already added to template {template_id}")
        
        # Create mapping
        mapping_model = TemplateTagMappingModel(
            template_id=template_id,
            tag_id=tag_id,
        )
        
        session.add(mapping_model)
        await session.commit()
        
        return True
    
    async def remove_tag_from_template(
        self,
        session: AsyncSession,
        template_id: UUID,
        tag_id: UUID
    ) -> bool:
        """
        Remove a tag from a template.
        
        Args:
            session: Database session
            template_id: Template ID
            tag_id: Tag ID
            
        Returns:
            bool: True if removed, False otherwise
            
        Raises:
            NotFoundException: If template, tag, or mapping not found
        """
        # Check if template exists
        template_query = select(AgentTemplateEngineModel).where(AgentTemplateEngineModel.id == template_id)
        template_result = await session.execute(template_query)
        template_model = template_result.scalars().first()
        
        if not template_model:
            raise NotFoundException(f"Template with ID {template_id} not found")
        
        # Check if tag exists
        tag_query = select(TemplateTagModel).where(TemplateTagModel.id == tag_id)
        tag_result = await session.execute(tag_query)
        tag_model = tag_result.scalars().first()
        
        if not tag_model:
            raise NotFoundException(f"Tag with ID {tag_id} not found")
        
        # Check if mapping exists
        mapping_query = select(TemplateTagMappingModel).where(
            TemplateTagMappingModel.template_id == template_id,
            TemplateTagMappingModel.tag_id == tag_id
        )
        mapping_result = await session.execute(mapping_query)
        mapping_model = mapping_result.scalars().first()
        
        if not mapping_model:
            raise NotFoundException(f"Tag {tag_id} not found on template {template_id}")
        
        # Delete mapping
        delete_query = delete(TemplateTagMappingModel).where(
            TemplateTagMappingModel.template_id == template_id,
            TemplateTagMappingModel.tag_id == tag_id
        )
        await session.execute(delete_query)
        await session.commit()
        
        return True
    
    async def get_template_tags(
        self,
        session: AsyncSession,
        template_id: UUID
    ) -> List[TemplateTag]:
        """
        Get all tags for a template.
        
        Args:
            session: Database session
            template_id: Template ID
            
        Returns:
            List[TemplateTag]: List of tags
            
        Raises:
            NotFoundException: If template not found
        """
        # Check if template exists
        template_query = select(AgentTemplateEngineModel).where(AgentTemplateEngineModel.id == template_id)
        template_result = await session.execute(template_query)
        template_model = template_result.scalars().first()
        
        if not template_model:
            raise NotFoundException(f"Template with ID {template_id} not found")
        
        # Get tags
        query = select(TemplateTagModel).join(
            TemplateTagMappingModel,
            TemplateTagMappingModel.tag_id == TemplateTagModel.id
        ).where(
            TemplateTagMappingModel.template_id == template_id
        ).order_by(TemplateTagModel.name)
        
        result = await session.execute(query)
        tag_models = result.scalars().all()
        
        return [self._tag_model_to_schema(model) for model in tag_models]
    
    async def track_template_usage(
        self,
        session: AsyncSession,
        template_id: UUID,
        success: bool = True
    ) -> None:
        """
        Track template usage for analytics.
        
        Args:
            session: Database session
            template_id: Template ID
            success: Whether the usage was successful
            
        Raises:
            NotFoundException: If template not found
        """
        # Check if template exists
        template_query = select(AgentTemplateEngineModel).where(AgentTemplateEngineModel.id == template_id)
        template_result = await session.execute(template_query)
        template_model = template_result.scalars().first()
        
        if not template_model:
            raise NotFoundException(f"Template with ID {template_id} not found")
        
        # Get analytics record
        analytics_query = select(TemplateAnalyticsModel).where(TemplateAnalyticsModel.template_id == template_id)
        analytics_result = await session.execute(analytics_query)
        analytics_model = analytics_result.scalars().first()
        
        if not analytics_model:
            # Create analytics record if it doesn't exist
            analytics_model = TemplateAnalyticsModel(
                template_id=template_id,
                usage_count=0,
                success_rate=1.0 if success else 0.0,
            )
            session.add(analytics_model)
        
        # Update analytics
        analytics_model.usage_count += 1
        analytics_model.last_used = datetime.utcnow()
        
        # Update success rate
        if analytics_model.success_rate is not None:
            # Calculate new success rate based on previous rate and new result
            previous_successes = analytics_model.success_rate * (analytics_model.usage_count - 1)
            new_successes = previous_successes + (1 if success else 0)
            analytics_model.success_rate = new_successes / analytics_model.usage_count
        else:
            analytics_model.success_rate = 1.0 if success else 0.0
        
        await session.commit()
    
    async def search_similar_templates(
        self,
        session: AsyncSession,
        content: Dict[str, Any]
    ) -> List[TemplateEngine]:
        """
        Search for similar templates based on content similarity.
        
        Args:
            session: Database session
            content: Template content to compare
            
        Returns:
            List[TemplateEngine]: List of similar templates
        """
        # Generate checksum for the content
        content_str = json.dumps(content, sort_keys=True)
        checksum = hashlib.sha256(content_str.encode()).hexdigest()
        
        # Search for templates with the same checksum
        query = select(AgentTemplateEngineModel).where(AgentTemplateEngineModel.checksum == checksum)
        result = await session.execute(query)
        template_models = result.scalars().all()
        
        # Convert to schemas
        templates = [self._model_to_schema(model) for model in template_models]
        
        return templates
    
    async def import_templates_from_files(
        self,
        session: AsyncSession,
        directory_path: str
    ) -> Tuple[int, int]:
        """
        Import templates from files in a directory.
        
        Args:
            session: Database session
            directory_path: Path to directory containing template files
            
        Returns:
            Tuple[int, int]: Number of templates imported and number of failures
        """
        if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
            raise ValidationException(f"Directory {directory_path} does not exist or is not a directory")
        
        imported_count = 0
        failed_count = 0
        
        # Get all JSON files in the directory
        json_files = [f for f in os.listdir(directory_path) if f.endswith('.json')]
        
        for file_name in json_files:
            file_path = os.path.join(directory_path, file_name)
            
            try:
                # Read template file
                with open(file_path, 'r') as f:
                    template_data = json.load(f)
                
                # Validate template data
                if not isinstance(template_data, dict):
                    logger.warning(f"Invalid template data in {file_path}: not a dictionary")
                    failed_count += 1
                    continue
                
                # Extract required fields
                name = template_data.get('name')
                template_type = template_data.get('template_type')
                base_agent_type = template_data.get('base_agent_type')
                template_content = template_data.get('template_content')
                
                if not name or not template_type or not base_agent_type or not template_content:
                    logger.warning(f"Missing required fields in {file_path}")
                    failed_count += 1
                    continue
                
                # Create template
                template = TemplateEngineCreate(
                    name=name,
                    description=template_data.get('description'),
                    template_type=template_type,
                    base_agent_type=base_agent_type,
                    template_content=template_content,
                    category=template_data.get('category'),
                    is_system_template=template_data.get('is_system_template', False),
                    is_public=template_data.get('is_public', False),
                )
                
                # Check if template already exists
                existing_query = select(AgentTemplateEngineModel).where(
                    AgentTemplateEngineModel.name == name,
                    AgentTemplateEngineModel.base_agent_type == base_agent_type
                )
                existing_result = await session.execute(existing_query)
                existing_model = existing_result.scalars().first()
                
                if existing_model:
                    logger.info(f"Template {name} for agent type {base_agent_type} already exists, skipping")
                    continue
                
                # Create template
                await self.create_template(session, template)
                imported_count += 1
                
            except Exception as e:
                logger.error(f"Error importing template from {file_path}: {str(e)}")
                failed_count += 1
        
        return imported_count, failed_count
    
    async def customize_template(
        self,
        session: AsyncSession,
        template_id: UUID,
        customization: TemplateCustomization
    ) -> Dict[str, Any]:
        """
        Apply customization to a template.
        
        Args:
            session: Database session
            template_id: Template ID
            customization: Customization values
            
        Returns:
            Dict[str, Any]: Customized template content
            
        Raises:
            NotFoundException: If template not found
        """
        # Get template
        query = select(AgentTemplateEngineModel).where(AgentTemplateEngineModel.id == template_id)
        result = await session.execute(query)
        template_model = result.scalars().first()
        
        if not template_model:
            raise NotFoundException(f"Template with ID {template_id} not found")
        
        # Apply customization
        template_content = template_model.template_content.copy()
        
        # Apply customization values
        for key, value in customization.customization_values.items():
            # Handle nested keys (e.g., "behavior.communication_style")
            if "." in key:
                parts = key.split(".")
                current = template_content
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                template_content[key] = value
        
        # Track template usage
        await self.track_template_usage(session, template_id)
        
        return template_content
    
    def _model_to_schema(self, model: AgentTemplateEngineModel) -> TemplateEngine:
        """
        Convert a database model to a schema.
        
        Args:
            model: Database model
            
        Returns:
            TemplateEngine: Schema
        """
        return TemplateEngine(
            id=model.id,
            name=model.name,
            description=model.description,
            template_type=model.template_type,
            base_agent_type=model.base_agent_type,
            template_content=model.template_content,
            category=model.category,
            is_system_template=model.is_system_template,
            is_public=model.is_public,
            owner_id=model.owner_id,
            checksum=model.checksum,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
    
    def _version_model_to_schema(self, model: AgentTemplateVersionModel) -> AgentTemplateVersion:
        """
        Convert a database version model to a schema.
        
        Args:
            model: Database model
            
        Returns:
            AgentTemplateVersion: Schema
        """
        return AgentTemplateVersion(
            id=model.id,
            template_id=model.template_id,
            version_number=model.version_number,
            template_content=model.template_content,
            changelog=model.changelog,
            created_by=model.created_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
    
    def _tag_model_to_schema(self, model: TemplateTagModel) -> TemplateTag:
        """
        Convert a database tag model to a schema.
        
        Args:
            model: Database model
            
        Returns:
            TemplateTag: Schema
        """
        return TemplateTag(
            id=model.id,
            name=model.name,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
    
    def _compare_json_objects(self, obj1: Dict[str, Any], obj2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare two JSON objects and return the differences.
        
        Args:
            obj1: First object
            obj2: Second object
            
        Returns:
            Dict[str, Any]: Differences
        """
        added = []
        removed = []
        changed = []
        
        # Find added and changed keys
        for key in obj2:
            if key not in obj1:
                added.append(key)
            elif obj1[key] != obj2[key]:
                if isinstance(obj1[key], dict) and isinstance(obj2[key], dict):
                    # Recursively compare nested objects
                    nested_diff = self._compare_json_objects(obj1[key], obj2[key])
                    for nested_key in nested_diff.get('added', []):
                        added.append(f"{key}.{nested_key}")
                    for nested_key in nested_diff.get('removed', []):
                        removed.append(f"{key}.{nested_key}")
                    for nested_key in nested_diff.get('changed', []):
                        changed.append(f"{key}.{nested_key}")
                else:
                    changed.append(key)
        
        # Find removed keys
        for key in obj1:
            if key not in obj2:
                removed.append(key)
        
        return {
            'added': added,
            'removed': removed,
            'changed': changed
        }
