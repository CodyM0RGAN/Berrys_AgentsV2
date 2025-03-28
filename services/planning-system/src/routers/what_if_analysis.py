"""
What-If Analysis router for the Planning System service.

This module implements API endpoints for what-if scenario analysis.
"""

from fastapi import APIRouter, Depends, Path, Query, HTTPException, status
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..models.api import (
    WhatIfScenarioCreate,
    WhatIfScenarioUpdate,
    WhatIfScenarioResponse,
    WhatIfScenarioListResponse,
    WhatIfAnalysisResult,
    WhatIfAnalysisResultResponse,
    PaginatedResponse
)
from ..services.what_if_analysis_service import WhatIfAnalysisService
from ..dependencies import get_what_if_analysis_service

router = APIRouter(
    prefix="/what-if",
    tags=["what-if-analysis"],
)

@router.post("/scenarios", response_model=WhatIfScenarioResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    scenario_data: WhatIfScenarioCreate,
    what_if_service: WhatIfAnalysisService = Depends(get_what_if_analysis_service),
):
    """
    Create a new what-if scenario.
    """
    return await what_if_service.create_scenario(scenario_data)

@router.get("/scenarios/{scenario_id}", response_model=WhatIfScenarioResponse)
async def get_scenario(
    scenario_id: UUID = Path(..., description="Scenario ID"),
    what_if_service: WhatIfAnalysisService = Depends(get_what_if_analysis_service),
):
    """
    Get a what-if scenario by ID.
    """
    return await what_if_service.get_scenario(scenario_id)

@router.get("/scenarios", response_model=PaginatedResponse)
async def list_scenarios(
    plan_id: UUID = Query(..., description="Plan ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    what_if_service: WhatIfAnalysisService = Depends(get_what_if_analysis_service),
):
    """
    List what-if scenarios for a plan with pagination.
    """
    return await what_if_service.list_scenarios(
        plan_id=plan_id,
        page=page,
        page_size=page_size
    )

@router.put("/scenarios/{scenario_id}", response_model=WhatIfScenarioResponse)
async def update_scenario(
    scenario_data: WhatIfScenarioUpdate,
    scenario_id: UUID = Path(..., description="Scenario ID"),
    what_if_service: WhatIfAnalysisService = Depends(get_what_if_analysis_service),
):
    """
    Update a what-if scenario.
    """
    return await what_if_service.update_scenario(scenario_id, scenario_data)

@router.delete("/scenarios/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario(
    scenario_id: UUID = Path(..., description="Scenario ID"),
    what_if_service: WhatIfAnalysisService = Depends(get_what_if_analysis_service),
):
    """
    Delete a what-if scenario.
    """
    await what_if_service.delete_scenario(scenario_id)
    return None

@router.post("/scenarios/{scenario_id}/analyze", response_model=WhatIfAnalysisResult)
async def run_what_if_analysis(
    scenario_id: UUID = Path(..., description="Scenario ID"),
    confidence_interval: Optional[float] = Query(None, ge=0, le=1, description="Confidence interval (0.0-1.0)"),
    what_if_service: WhatIfAnalysisService = Depends(get_what_if_analysis_service),
):
    """
    Run what-if analysis for a scenario.
    """
    return await what_if_service.run_what_if_analysis(
        scenario_id=scenario_id,
        confidence_interval=confidence_interval
    )

@router.post("/scenarios/compare", response_model=Dict[str, Any])
async def compare_scenarios(
    scenario_id_1: UUID = Query(..., description="First scenario ID"),
    scenario_id_2: UUID = Query(..., description="Second scenario ID"),
    what_if_service: WhatIfAnalysisService = Depends(get_what_if_analysis_service),
):
    """
    Compare two what-if scenarios.
    """
    return await what_if_service.compare_scenarios(
        scenario_id_1=scenario_id_1,
        scenario_id_2=scenario_id_2
    )

@router.post("/scenarios/{scenario_id}/apply", response_model=Dict[str, Any])
async def apply_scenario_to_plan(
    scenario_id: UUID = Path(..., description="Scenario ID"),
    what_if_service: WhatIfAnalysisService = Depends(get_what_if_analysis_service),
):
    """
    Apply a what-if scenario to the actual plan.
    """
    return await what_if_service.apply_scenario_to_plan(scenario_id)
