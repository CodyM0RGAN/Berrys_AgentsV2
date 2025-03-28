"""
Model management functionality.

This module contains the ModelManagementMixin class that provides methods for managing models.
"""

import logging
from sqlalchemy import select, and_
from typing import List, Optional, Tuple, Dict, Any

from ...exceptions import ModelNotFoundError, InvalidRequestError, ProviderNotAvailableError
# Updated imports to use shared enums
from shared.models.src.enums import ModelProvider, ModelCapability, ModelStatus
from ...models.api import ModelCreate, ModelUpdate, Model
from ...models.internal import ModelModel

logger = logging.getLogger(__name__)


class ModelManagementMixin:
    """
    Mixin for model management operations.
    
    This mixin provides methods for:
    - Registering models
    - Retrieving models
    - Listing models
    - Updating models
    - Deleting models
    """
    
    async def register_model(self, model_data: ModelCreate) -> Model:
        """
        Register a new model.
        
        Args:
            model_data: Model data
            
        Returns:
            Model: Registered model
            
        Raises:
            InvalidRequestError: If model data is invalid
            ProviderNotAvailableError: If provider is not available
        """
        try:
            # Check if model already exists
            query = select(ModelModel).where(ModelModel.model_id == model_data.model_id)
            result = await self.db.execute(query)
            existing_model = result.scalars().first()
            
            if existing_model:
                raise InvalidRequestError(f"Model '{model_data.model_id}' already exists")
            
            # Get provider
            try:
                provider = await self.provider_factory.get_provider(model_data.provider.value)
            except ProviderNotAvailableError as e:
                raise ProviderNotAvailableError(str(model_data.provider.value), f"Provider '{model_data.provider.value}' is not available")
            
            # Check if provider supports model
            if not provider.supports_model(model_data.model_id):
                # Allow registration anyway, but log a warning
                logger.warning(f"Provider '{model_data.provider.value}' does not explicitly support model '{model_data.model_id}'")
            
            # Create model
            model_model = ModelModel(
                model_id=model_data.model_id,
                provider=model_data.provider,
                display_name=model_data.display_name or model_data.model_id,
                description=model_data.description,
                capabilities=[cap.value for cap in model_data.capabilities],
                status=model_data.status,
                max_tokens=model_data.max_tokens,
                token_limit=model_data.token_limit,
                cost_per_token=model_data.cost_per_token,
                configuration=model_data.configuration,
                metadata=model_data.metadata,
            )
            
            # Add to database
            self.db.add(model_model)
            await self.db.commit()
            await self.db.refresh(model_model)
            
            # Convert to API model
            model = Model(
                id=model_model.id,
                model_id=model_model.model_id,
                provider=model_model.provider,
                display_name=model_model.display_name,
                description=model_model.description,
                capabilities=[ModelCapability(cap) for cap in model_model.capabilities],
                status=model_model.status,
                max_tokens=model_model.max_tokens,
                token_limit=model_model.token_limit,
                cost_per_token=model_model.cost_per_token,
                configuration=model_model.configuration or {},
                metadata=model_model.metadata or {},
                created_at=model_model.created_at,
                updated_at=model_model.updated_at,
            )
            
            # Publish event
            await self.event_bus.publish_event(
                "model.registered",
                {
                    "model_id": model.model_id,
                    "provider": model.provider.value,
                    "capabilities": [cap.value for cap in model.capabilities],
                }
            )
            
            return model
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error registering model: {str(e)}")
            
            if isinstance(e, (InvalidRequestError, ProviderNotAvailableError)):
                raise
            
            raise InvalidRequestError(f"Failed to register model: {str(e)}")
    
    async def get_model(self, model_id: str) -> Optional[Model]:
        """
        Get a model by ID.
        
        Args:
            model_id: Model ID
            
        Returns:
            Optional[Model]: Model if found, None otherwise
        """
        try:
            # Query model
            query = select(ModelModel).where(ModelModel.model_id == model_id)
            result = await self.db.execute(query)
            model_model = result.scalars().first()
            
            # Return None if not found
            if not model_model:
                return None
            
            # Convert to API model
            model = Model(
                id=model_model.id,
                model_id=model_model.model_id,
                provider=model_model.provider,
                display_name=model_model.display_name,
                description=model_model.description,
                capabilities=[ModelCapability(cap) for cap in model_model.capabilities],
                status=model_model.status,
                max_tokens=model_model.max_tokens,
                token_limit=model_model.token_limit,
                cost_per_token=model_model.cost_per_token,
                configuration=model_model.configuration or {},
                metadata=model_model.metadata or {},
                created_at=model_model.created_at,
                updated_at=model_model.updated_at,
            )
            
            return model
        except Exception as e:
            logger.error(f"Error getting model {model_id}: {str(e)}")
            return None
    
    async def list_models(
        self,
        page: int = 1,
        page_size: int = 20,
        provider: Optional[str] = None,
        capability: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Model], int]:
        """
        List models with pagination and filtering.
        
        Args:
            page: Page number
            page_size: Page size
            provider: Filter by provider
            capability: Filter by capability
            status: Filter by status
            search: Search term
            
        Returns:
            Tuple[List[Model], int]: List of models and total count
        """
        try:
            from sqlalchemy import func, or_, and_
            
            # Build query
            query = select(ModelModel)
            count_query = select(func.count()).select_from(ModelModel)
            
            # Apply filters
            filters = []
            
            if provider:
                try:
                    provider_enum = ModelProvider(provider)
                    filters.append(ModelModel.provider == provider_enum)
                except ValueError:
                    # Invalid provider, ignore filter
                    pass
            
            if capability:
                filters.append(ModelModel.capabilities.contains([capability]))
            
            if status:
                try:
                    status_enum = ModelStatus(status)
                    filters.append(ModelModel.status == status_enum)
                except ValueError:
                    # Invalid status, ignore filter
                    pass
            
            if search:
                search_filter = or_(
                    ModelModel.model_id.ilike(f"%{search}%"),
                    ModelModel.display_name.ilike(f"%{search}%"),
                    ModelModel.description.ilike(f"%{search}%"),
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
            model_models = result.scalars().all()
            
            # Convert to API models
            models = []
            for model_model in model_models:
                model = Model(
                    id=model_model.id,
                    model_id=model_model.model_id,
                    provider=model_model.provider,
                    display_name=model_model.display_name,
                    description=model_model.description,
                    capabilities=[ModelCapability(cap) for cap in model_model.capabilities],
                    status=model_model.status,
                    max_tokens=model_model.max_tokens,
                    token_limit=model_model.token_limit,
                    cost_per_token=model_model.cost_per_token,
                    configuration=model_model.configuration or {},
                    metadata=model_model.metadata or {},
                    created_at=model_model.created_at,
                    updated_at=model_model.updated_at,
                )
                models.append(model)
            
            return models, total
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return [], 0
    
    async def update_model(self, model_id: str, model_update: ModelUpdate) -> Model:
        """
        Update a model.
        
        Args:
            model_id: Model ID
            model_update: Model update data
            
        Returns:
            Model: Updated model
            
        Raises:
            ModelNotFoundError: If model not found
            InvalidRequestError: If model data is invalid
        """
        try:
            # Query model
            query = select(ModelModel).where(ModelModel.model_id == model_id)
            result = await self.db.execute(query)
            model_model = result.scalars().first()
            
            # Check if model exists
            if not model_model:
                raise ModelNotFoundError(model_id)
            
            # Update fields
            update_data = model_update.dict(exclude_unset=True)
            
            # Handle capabilities separately
            if "capabilities" in update_data:
                model_model.capabilities = [cap.value for cap in update_data["capabilities"]]
                del update_data["capabilities"]
            
            # Update other fields
            for key, value in update_data.items():
                setattr(model_model, key, value)
            
            # Commit changes
            await self.db.commit()
            await self.db.refresh(model_model)
            
            # Convert to API model
            model = Model(
                id=model_model.id,
                model_id=model_model.model_id,
                provider=model_model.provider,
                display_name=model_model.display_name,
                description=model_model.description,
                capabilities=[ModelCapability(cap) for cap in model_model.capabilities],
                status=model_model.status,
                max_tokens=model_model.max_tokens,
                token_limit=model_model.token_limit,
                cost_per_token=model_model.cost_per_token,
                configuration=model_model.configuration or {},
                metadata=model_model.metadata or {},
                created_at=model_model.created_at,
                updated_at=model_model.updated_at,
            )
            
            # Publish event
            await self.event_bus.publish_event(
                "model.updated",
                {
                    "model_id": model.model_id,
                    "provider": model.provider.value,
                    "updated_fields": list(update_data.keys()),
                }
            )
            
            return model
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating model {model_id}: {str(e)}")
            
            if isinstance(e, ModelNotFoundError):
                raise
            
            raise InvalidRequestError(f"Failed to update model: {str(e)}")
    
    async def delete_model(self, model_id: str) -> None:
        """
        Delete a model.
        
        Args:
            model_id: Model ID
            
        Raises:
            ModelNotFoundError: If model not found
        """
        try:
            # Query model
            query = select(ModelModel).where(ModelModel.model_id == model_id)
            result = await self.db.execute(query)
            model_model = result.scalars().first()
            
            # Check if model exists
            if not model_model:
                raise ModelNotFoundError(model_id)
            
            # Store model data for event
            model_data = {
                "model_id": model_model.model_id,
                "provider": model_model.provider.value,
            }
            
            # Delete model
            await self.db.delete(model_model)
            await self.db.commit()
            
            # Publish event
            await self.event_bus.publish_event(
                "model.deleted",
                model_data
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting model {model_id}: {str(e)}")
            
            if isinstance(e, ModelNotFoundError):
                raise
            
            raise InvalidRequestError(f"Failed to delete model: {str(e)}")
