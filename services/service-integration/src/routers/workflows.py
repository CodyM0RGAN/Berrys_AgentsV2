"""
Workflows Router.

This module provides API endpoints for executing cross-service workflows.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from ..models.api import (
    WorkflowRequest, WorkflowResponse, WorkflowType
)
from ..services.integration_facade import SystemIntegrationFacade
from ..exceptions import WorkflowError, UnknownRequestTypeError
from ..dependencies import get_integration_facade, register_workflow_handlers


router = APIRouter(
    prefix="/workflows",
    tags=["Workflows"],
    responses={500: {"description": "Workflow execution error"}},
)


# Register workflow handlers when the module is loaded
@router.on_event("startup")
async def startup_event():
    """Register workflow handlers when the application starts."""
    # This will be called when the application starts
    # and will register all the workflow handlers with the mediator
    register_workflow_handlers()


@router.post("/execute", response_model=WorkflowResponse)
async def execute_workflow(
    workflow_request: WorkflowRequest,
    facade: SystemIntegrationFacade = Depends(get_integration_facade)
):
    """
    Execute a cross-service workflow.
    
    This endpoint executes a workflow that coordinates operations
    across multiple services to accomplish a complex task.
    """
    try:
        return await facade.execute_workflow(workflow_request)
    except UnknownRequestTypeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown workflow type: {workflow_request.workflow_type}"
        )
    except WorkflowError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/agent-task-execution", response_model=WorkflowResponse)
async def execute_agent_task_workflow(
    request: Dict[str, Any],
    facade: SystemIntegrationFacade = Depends(get_integration_facade)
):
    """
    Execute an agent task workflow.
    
    This is a convenience endpoint for executing the agent task execution workflow.
    """
    workflow_request = WorkflowRequest(
        workflow_type=WorkflowType.AGENT_TASK_EXECUTION,
        data=request
    )
    
    try:
        return await facade.execute_workflow(workflow_request)
    except WorkflowError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/project-planning", response_model=WorkflowResponse)
async def execute_project_planning_workflow(
    request: Dict[str, Any],
    facade: SystemIntegrationFacade = Depends(get_integration_facade)
):
    """
    Execute a project planning workflow.
    
    This is a convenience endpoint for executing the project planning workflow.
    """
    workflow_request = WorkflowRequest(
        workflow_type=WorkflowType.PROJECT_PLANNING,
        data=request
    )
    
    try:
        return await facade.execute_workflow(workflow_request)
    except WorkflowError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
