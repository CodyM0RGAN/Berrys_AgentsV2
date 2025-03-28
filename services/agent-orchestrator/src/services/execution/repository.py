"""
Repository component for the Execution service.

This module provides the data access layer for execution operations.
"""

import logging
from sqlalchemy import select, update, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime

from ...models.internal import AgentExecutionModel, ExecutionStateModel
from ...models.api import ExecutionState
from ...exceptions import DatabaseError

logger = logging.getLogger(__name__)

class ExecutionRepository:
    """
    Handles all database operations for executions.
    """
    def __init__(self, db: AsyncSession):
        """
        Initialize the repository.
        
        Args:
            db: Database session
        """
        self.db = db
        
    async def get_by_id(self, execution_id: UUID) -> Optional[AgentExecutionModel]:
        """
        Get an execution by ID.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Optional[AgentExecutionModel]: Execution if found, None otherwise
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = select(AgentExecutionModel).where(AgentExecutionModel.id == execution_id)
            result = await self.db.execute(query)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting execution {execution_id}: {str(e)}")
            raise DatabaseError(f"Failed to get execution: {str(e)}")
        
    async def list_executions(
        self,
        filters: Dict[str, Any],
        pagination: Dict[str, int]
    ) -> Tuple[List[AgentExecutionModel], int]:
        """
        List executions with filtering and pagination.
        
        Args:
            filters: Dictionary of filter parameters (agent_id, task_id, state)
            pagination: Dictionary with page and page_size
            
        Returns:
            Tuple[List[AgentExecutionModel], int]: List of executions and total count
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Build query
            query = select(AgentExecutionModel)
            count_query = select(func.count()).select_from(AgentExecutionModel)
            
            # Apply filters
            filter_clauses = []
            
            if filters.get("agent_id"):
                filter_clauses.append(AgentExecutionModel.agent_id == filters["agent_id"])
            
            if filters.get("task_id"):
                filter_clauses.append(AgentExecutionModel.task_id == filters["task_id"])
            
            if filters.get("state"):
                filter_clauses.append(AgentExecutionModel.state == filters["state"])
            
            # Apply filters to queries
            if filter_clauses:
                filter_clause = and_(*filter_clauses)
                query = query.where(filter_clause)
                count_query = count_query.where(filter_clause)
            
            # Get total count
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()
            
            # Apply pagination and ordering
            page = pagination.get("page", 1)
            page_size = pagination.get("page_size", 20)
            
            query = (
                query
                .order_by(AgentExecutionModel.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            
            # Execute query
            result = await self.db.execute(query)
            executions = result.scalars().all()
            
            return list(executions), total
        except Exception as e:
            logger.error(f"Error listing executions: {str(e)}")
            raise DatabaseError(f"Failed to list executions: {str(e)}")
        
    async def update_state(
        self,
        execution_id: UUID,
        state: ExecutionState,
        timestamps: Dict[str, datetime] = None,
        optimistic_locking_condition: Optional[ExecutionState] = None
    ) -> Optional[AgentExecutionModel]:
        """
        Update execution state.
        
        Args:
            execution_id: Execution ID
            state: New state
            timestamps: Optional timestamps to update (e.g., started_at, completed_at)
            optimistic_locking_condition: If provided, ensure the current state
                                         matches this value before updating
            
        Returns:
            Optional[AgentExecutionModel]: Updated execution if successful, None if not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Prepare update values
            values = {
                "state": state,
                "updated_at": datetime.utcnow(),
            }
            
            # Add any additional timestamps
            if timestamps:
                values.update(timestamps)
            
            # Build update statement
            stmt = update(AgentExecutionModel).where(AgentExecutionModel.id == execution_id)
            
            # Add optimistic locking condition if provided
            if optimistic_locking_condition:
                stmt = stmt.where(AgentExecutionModel.state == optimistic_locking_condition)
                
            # Update
            stmt = stmt.values(**values).returning(AgentExecutionModel)
            result = await self.db.execute(stmt)
            updated_execution = result.scalar_one_or_none()
            
            if updated_execution:
                await self.db.commit()
                return updated_execution
            return None
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating execution state for {execution_id}: {str(e)}")
            raise DatabaseError(f"Failed to update execution state: {str(e)}")
        
    async def update_progress(
        self,
        execution_id: UUID,
        percentage: float,
        message: str,
        context_update: Dict[str, Any] = None
    ) -> Optional[AgentExecutionModel]:
        """
        Update execution progress.
        
        Args:
            execution_id: Execution ID
            percentage: Progress percentage (0-100)
            message: Status message
            context_update: Optional context update
            
        Returns:
            Optional[AgentExecutionModel]: Updated execution if successful, None if not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Get the execution
            execution = await self.get_by_id(execution_id)
            
            if not execution:
                return None
            
            # Update execution
            execution.progress_percentage = percentage
            execution.status_message = message
            execution.updated_at = datetime.utcnow()
            
            # Update context if provided
            if context_update:
                context = execution.context or {}
                context.update(context_update)
                execution.context = context
            
            await self.db.commit()
            await self.db.refresh(execution)
            
            return execution
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating execution progress for {execution_id}: {str(e)}")
            raise DatabaseError(f"Failed to update execution progress: {str(e)}")
        
    async def update_result(
        self,
        execution_id: UUID,
        result: Dict[str, Any],
        error_message: Optional[str] = None
    ) -> Optional[AgentExecutionModel]:
        """
        Update execution result.
        
        Args:
            execution_id: Execution ID
            result: Execution result
            error_message: Optional error message
            
        Returns:
            Optional[AgentExecutionModel]: Updated execution if successful, None if not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Get the execution
            execution = await self.get_by_id(execution_id)
            
            if not execution:
                return None
            
            # Update execution
            execution.result = result
            execution.error_message = error_message
            execution.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(execution)
            
            return execution
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating execution result for {execution_id}: {str(e)}")
            raise DatabaseError(f"Failed to update execution result: {str(e)}")
        
    async def create_state_history(
        self,
        execution_id: UUID,
        previous_state: ExecutionState,
        new_state: ExecutionState,
        reason: Optional[str] = None
    ) -> ExecutionStateModel:
        """
        Create execution state history entry.
        
        Args:
            execution_id: Execution ID
            previous_state: Previous state
            new_state: New state
            reason: Reason for state change
            
        Returns:
            ExecutionStateModel: Created history item
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Create history item
            history_item = ExecutionStateModel(
                execution_id=execution_id,
                previous_state=previous_state,
                new_state=new_state,
                reason=reason,
            )
            
            self.db.add(history_item)
            await self.db.commit()
            await self.db.refresh(history_item)
            
            return history_item
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating state history for {execution_id}: {str(e)}")
            raise DatabaseError(f"Failed to create state history: {str(e)}")
        
    async def get_state_history(
        self,
        execution_id: UUID,
        limit: int = 10
    ) -> List[ExecutionStateModel]:
        """
        Get execution state history.
        
        Args:
            execution_id: Execution ID
            limit: Maximum number of history entries to return
            
        Returns:
            List[ExecutionStateModel]: Execution state history
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Query state history
            query = (
                select(ExecutionStateModel)
                .where(ExecutionStateModel.execution_id == execution_id)
                .order_by(ExecutionStateModel.timestamp.desc())
                .limit(limit)
            )
            
            result = await self.db.execute(query)
            state_history = result.scalars().all()
            
            return list(state_history)
        except Exception as e:
            logger.error(f"Error getting execution state history for {execution_id}: {str(e)}")
            raise DatabaseError(f"Failed to get execution state history: {str(e)}")
        
    async def delete_execution(self, execution_id: UUID) -> bool:
        """
        Delete an execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            bool: True if deleted, False if not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Get the execution
            execution = await self.get_by_id(execution_id)
            
            if not execution:
                return False
            
            # Delete execution
            await self.db.delete(execution)
            await self.db.commit()
            
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting execution {execution_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete execution: {str(e)}")
