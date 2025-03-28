"""
Metrics router for the Agent Communication Hub Monitoring and Analytics feature.

This module provides API endpoints for accessing metrics data collected by the
MetricsCollector component.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db, get_enhanced_communication_service
from ..services.enhanced_communication_service import EnhancedCommunicationService
from ..models.metrics import MessageStatus

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/metrics",
    tags=["metrics"],
    responses={404: {"description": "Not found"}},
)


@router.get("/messages", response_model=List[Dict[str, Any]])
async def get_message_metrics(
    message_id: Optional[UUID] = None,
    source_agent_id: Optional[UUID] = None,
    destination_agent_id: Optional[UUID] = None,
    topic: Optional[str] = None,
    status: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    communication_service: EnhancedCommunicationService = Depends(get_enhanced_communication_service),
):
    """
    Get message metrics.
    
    Args:
        message_id: Filter by message ID
        source_agent_id: Filter by source agent ID
        destination_agent_id: Filter by destination agent ID
        topic: Filter by topic
        status: Filter by status
        start_time: Filter by start time
        end_time: Filter by end time
        limit: Maximum number of results
        offset: Offset for pagination
        communication_service: Enhanced communication service
        
    Returns:
        List of message metrics
    """
    try:
        # Convert status string to enum if provided
        status_enum = None
        if status:
            try:
                status_enum = MessageStatus(status.upper())
            except ValueError:
                valid_statuses = [s.value for s in MessageStatus]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}. Valid values are: {', '.join(valid_statuses)}"
                )
        
        # Set default time range if not provided
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(days=1)
        
        # Get message metrics
        metrics = await communication_service.metrics_collector.get_message_metrics(
            message_id=message_id,
            source_agent_id=source_agent_id,
            destination_agent_id=destination_agent_id,
            topic=topic,
            status=status_enum,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset
        )
        
        return metrics
    except Exception as e:
        logger.error(f"Error getting message metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get message metrics: {str(e)}"
        )


@router.get("/agents", response_model=List[Dict[str, Any]])
async def get_agent_metrics(
    agent_id: Optional[UUID] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    communication_service: EnhancedCommunicationService = Depends(get_enhanced_communication_service),
):
    """
    Get agent metrics.
    
    Args:
        agent_id: Filter by agent ID
        start_time: Filter by start time
        end_time: Filter by end time
        limit: Maximum number of results
        offset: Offset for pagination
        communication_service: Enhanced communication service
        
    Returns:
        List of agent metrics
    """
    try:
        # Set default time range if not provided
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(days=1)
        
        # Get agent metrics
        metrics = await communication_service.metrics_collector.get_agent_metrics(
            agent_id=agent_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset
        )
        
        return metrics
    except Exception as e:
        logger.error(f"Error getting agent metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent metrics: {str(e)}"
        )


@router.get("/topics", response_model=List[Dict[str, Any]])
async def get_topic_metrics(
    topic: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    communication_service: EnhancedCommunicationService = Depends(get_enhanced_communication_service),
):
    """
    Get topic metrics.
    
    Args:
        topic: Filter by topic
        start_time: Filter by start time
        end_time: Filter by end time
        limit: Maximum number of results
        offset: Offset for pagination
        communication_service: Enhanced communication service
        
    Returns:
        List of topic metrics
    """
    try:
        # Set default time range if not provided
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(days=1)
        
        # Get topic metrics
        metrics = await communication_service.metrics_collector.get_topic_metrics(
            topic=topic,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset
        )
        
        return metrics
    except Exception as e:
        logger.error(f"Error getting topic metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get topic metrics: {str(e)}"
        )


@router.get("/performance", response_model=Dict[str, Any])
async def get_performance_metrics(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    communication_service: EnhancedCommunicationService = Depends(get_enhanced_communication_service),
):
    """
    Get performance metrics.
    
    Args:
        start_time: Filter by start time
        end_time: Filter by end time
        communication_service: Enhanced communication service
        
    Returns:
        Performance metrics
    """
    try:
        # Set default time range if not provided
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(days=1)
        
        # Get performance metrics
        metrics = await communication_service.metrics_collector.get_performance_metrics(
            start_time=start_time,
            end_time=end_time
        )
        
        return metrics
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}"
        )
