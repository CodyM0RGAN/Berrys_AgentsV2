"""
Forecasts router for the Planning System service.

This module defines the FastAPI routes for forecast management,
including generating and retrieving timeline forecasts.
"""

import logging
from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status

from ..dependencies import get_planning_service
from ..models.api import (
    TimelineForecast,
    ForecastRequest,
    BottleneckAnalysis,
    PaginatedResponse,
    PaginationParams
)
from ..services.planning_service import PlanningService
from ..exceptions import PlanNotFoundError, ForecastingError, InsufficientDataError

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/timeline", response_model=TimelineForecast)
async def generate_timeline_forecast(
    forecast_request: ForecastRequest,
    service: PlanningService = Depends(get_planning_service)
):
    """
    Generate a timeline forecast for a plan.
    
    Args:
        forecast_request: Forecast request data
        service: Planning service
        
    Returns:
        TimelineForecast: Generated forecast
        
    Raises:
        HTTPException: If forecast generation fails
    """
    logger.info(f"Generating timeline forecast for plan: {forecast_request.plan_id}")
    try:
        return await service.generate_timeline_forecast(forecast_request)
    except PlanNotFoundError:
        logger.error(f"Plan not found: {forecast_request.plan_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {forecast_request.plan_id}"
        )
    except InsufficientDataError as e:
        logger.error(f"Insufficient data for forecasting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient data for forecasting: {str(e)}"
        )
    except ForecastingError as e:
        logger.error(f"Forecasting error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecasting error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error generating timeline forecast: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating timeline forecast: {str(e)}"
        )

@router.get("/timeline/{plan_id}", response_model=TimelineForecast)
async def get_latest_timeline_forecast(
    plan_id: UUID = Path(..., description="Plan ID"),
    service: PlanningService = Depends(get_planning_service)
):
    """
    Get the latest timeline forecast for a plan.
    
    Args:
        plan_id: Plan ID
        service: Planning service
        
    Returns:
        TimelineForecast: Latest forecast
        
    Raises:
        HTTPException: If forecast not found
    """
    logger.info(f"Getting latest timeline forecast for plan: {plan_id}")
    try:
        forecast = await service.get_latest_timeline_forecast(plan_id)
        if not forecast:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No forecast found for plan: {plan_id}"
            )
        return forecast
    except PlanNotFoundError:
        logger.error(f"Plan not found: {plan_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}"
        )
    except Exception as e:
        logger.error(f"Error getting latest timeline forecast: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting latest timeline forecast: {str(e)}"
        )

@router.get("/timeline/{plan_id}/history", response_model=PaginatedResponse)
async def get_forecast_history(
    plan_id: UUID = Path(..., description="Plan ID"),
    pagination: PaginationParams = Depends(),
    service: PlanningService = Depends(get_planning_service)
):
    """
    Get the history of timeline forecasts for a plan.
    
    Args:
        plan_id: Plan ID
        pagination: Pagination parameters
        service: Planning service
        
    Returns:
        PaginatedResponse: Paginated list of forecasts
        
    Raises:
        HTTPException: If getting forecast history fails
    """
    logger.info(f"Getting forecast history for plan: {plan_id}")
    try:
        return await service.get_forecast_history(
            plan_id=plan_id,
            page=pagination.page,
            page_size=pagination.page_size
        )
    except PlanNotFoundError:
        logger.error(f"Plan not found: {plan_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}"
        )
    except Exception as e:
        logger.error(f"Error getting forecast history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting forecast history: {str(e)}"
        )

@router.post("/bottlenecks", response_model=BottleneckAnalysis)
async def analyze_bottlenecks(
    plan_id: UUID,
    options: Optional[Dict[str, Any]] = None,
    service: PlanningService = Depends(get_planning_service)
):
    """
    Analyze bottlenecks in a plan.
    
    Args:
        plan_id: Plan ID
        options: Optional analysis options
        service: Planning service
        
    Returns:
        BottleneckAnalysis: Bottleneck analysis
        
    Raises:
        HTTPException: If bottleneck analysis fails
    """
    logger.info(f"Analyzing bottlenecks for plan: {plan_id}")
    try:
        return await service.analyze_bottlenecks(plan_id, options or {})
    except PlanNotFoundError:
        logger.error(f"Plan not found: {plan_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}"
        )
    except InsufficientDataError as e:
        logger.error(f"Insufficient data for bottleneck analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient data for bottleneck analysis: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error analyzing bottlenecks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing bottlenecks: {str(e)}"
        )

@router.get("/critical-path/{plan_id}", response_model=Dict[str, Any])
async def get_critical_path(
    plan_id: UUID = Path(..., description="Plan ID"),
    service: PlanningService = Depends(get_planning_service)
):
    """
    Get the critical path for a plan.
    
    Args:
        plan_id: Plan ID
        service: Planning service
        
    Returns:
        Dict[str, Any]: Critical path data
        
    Raises:
        HTTPException: If getting critical path fails
    """
    logger.info(f"Getting critical path for plan: {plan_id}")
    try:
        return await service.get_critical_path(plan_id)
    except PlanNotFoundError:
        logger.error(f"Plan not found: {plan_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}"
        )
    except Exception as e:
        logger.error(f"Error getting critical path: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting critical path: {str(e)}"
        )

@router.get("/slack-analysis/{plan_id}", response_model=Dict[str, Any])
async def get_slack_analysis(
    plan_id: UUID = Path(..., description="Plan ID"),
    service: PlanningService = Depends(get_planning_service)
):
    """
    Get slack analysis for a plan.
    
    Args:
        plan_id: Plan ID
        service: Planning service
        
    Returns:
        Dict[str, Any]: Slack analysis data
        
    Raises:
        HTTPException: If getting slack analysis fails
    """
    logger.info(f"Getting slack analysis for plan: {plan_id}")
    try:
        return await service.get_slack_analysis(plan_id)
    except PlanNotFoundError:
        logger.error(f"Plan not found: {plan_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}"
        )
    except Exception as e:
        logger.error(f"Error getting slack analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting slack analysis: {str(e)}"
        )
