"""
Base repository implementation for Project Coordinator service.

This module provides a generic repository pattern implementation that other repositories
can extend for specific entity types.
"""
from typing import Generic, TypeVar, Type, List, Optional, Dict, Any, Union
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from pydantic import BaseModel

from ..models.internal import Base

# Type variables for generics
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base repository with default CRUD operations.
    
    Provides generic CRUD operations for a SQLAlchemy model. This class can be
    extended for specific entity types to provide custom operations.
    
    Attributes:
        model: The SQLAlchemy model class this repository handles
        db: SQLAlchemy session
    """
    
    def __init__(self, db: Session, model: Type[ModelType]):
        """
        Initialize the repository with database session and model class.
        
        Args:
            db: SQLAlchemy session
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model
    
    def get(self, id: Union[UUID, str]) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        Args:
            id: Record ID
            
        Returns:
            The record if found, None otherwise
        """
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """
        Get multiple records with optional filtering, pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional dictionary of field-value pairs to filter by
            
        Returns:
            List of records
        """
        query = self.db.query(self.model)
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
        
        return query.offset(skip).limit(limit).all()
    
    def create(self, *, obj_in: Union[CreateSchemaType, Dict[str, Any]]) -> ModelType:
        """
        Create a new record.
        
        Args:
            obj_in: Data to create record with
            
        Returns:
            The created record
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def update(
        self,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update a record.
        
        Args:
            db_obj: Database object to update
            obj_in: Data to update record with
            
        Returns:
            The updated record
        """
        obj_data = jsonable_encoder(db_obj)
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, *, id: Union[UUID, str]) -> ModelType:
        """
        Delete a record.
        
        Args:
            id: Record ID
            
        Returns:
            The deleted record
        """
        obj = self.db.query(self.model).get(id)
        self.db.delete(obj)
        self.db.commit()
        return obj
    
    def count(self, *, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records with optional filtering.
        
        Args:
            filters: Optional dictionary of field-value pairs to filter by
            
        Returns:
            Count of records
        """
        query = self.db.query(self.model)
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
        
        return query.count()
