"""
API client initialization and management.
"""
import logging
from typing import Dict, Optional

from flask import current_app, g

# Import synchronized client implementations
from shared.utils.src.clients import (
    SyncAgentOrchestratorClient,
    SyncModelOrchestrationClient,
    SyncPlanningSystemClient,
    SyncProjectCoordinatorClient,
    SyncServiceIntegrationClient,
    SyncToolIntegrationClient
)

# Set up logger
logger = logging.getLogger(__name__)

def init_api_clients(app) -> None:
    """
    Initialize API clients for the application.
    
    Args:
        app: Flask application instance
    """
    # Log API endpoints
    logger.info(f"Agent Orchestrator API URL: {app.config.get('AGENT_ORCHESTRATOR_API_URL')}")
    logger.info(f"Project Coordinator API URL: {app.config.get('PROJECT_COORDINATOR_API_URL')}")
    logger.info(f"Model Orchestration API URL: {app.config.get('MODEL_ORCHESTRATION_API_URL')}")
    logger.info(f"Planning System API URL: {app.config.get('PLANNING_SYSTEM_API_URL')}")
    logger.info(f"Service Integration API URL: {app.config.get('SERVICE_INTEGRATION_API_URL')}")
    logger.info(f"Tool Integration API URL: {app.config.get('TOOL_INTEGRATION_API_URL')}")

def get_agent_orchestrator_client() -> SyncAgentOrchestratorClient:
    """
    Get or create an Agent Orchestrator API client.
    
    Returns:
        SyncAgentOrchestratorClient instance
    """
    if 'agent_orchestrator_client' not in g:
        base_url = current_app.config.get('AGENT_ORCHESTRATOR_API_URL')
        timeout = current_app.config.get('API_TIMEOUT')
        g.agent_orchestrator_client = SyncAgentOrchestratorClient(base_url, timeout)
    
    return g.agent_orchestrator_client

def get_project_coordinator_client() -> SyncProjectCoordinatorClient:
    """
    Get or create a Project Coordinator API client.
    
    Returns:
        SyncProjectCoordinatorClient instance
    """
    if 'project_coordinator_client' not in g:
        base_url = current_app.config.get('PROJECT_COORDINATOR_API_URL')
        timeout = current_app.config.get('API_TIMEOUT')
        g.project_coordinator_client = SyncProjectCoordinatorClient(base_url, timeout)
    
    return g.project_coordinator_client

def get_model_orchestration_client() -> SyncModelOrchestrationClient:
    """
    Get or create a Model Orchestration API client.
    
    Returns:
        SyncModelOrchestrationClient instance
    """
    if 'model_orchestration_client' not in g:
        base_url = current_app.config.get('MODEL_ORCHESTRATION_API_URL')
        timeout = current_app.config.get('API_TIMEOUT')
        g.model_orchestration_client = SyncModelOrchestrationClient(base_url, timeout)
    
    return g.model_orchestration_client

def get_planning_system_client() -> SyncPlanningSystemClient:
    """
    Get or create a Planning System API client.
    
    Returns:
        SyncPlanningSystemClient instance
    """
    if 'planning_system_client' not in g:
        base_url = current_app.config.get('PLANNING_SYSTEM_API_URL')
        timeout = current_app.config.get('API_TIMEOUT')
        g.planning_system_client = SyncPlanningSystemClient(base_url, timeout)
    
    return g.planning_system_client

def get_service_integration_client() -> SyncServiceIntegrationClient:
    """
    Get or create a Service Integration API client.
    
    Returns:
        SyncServiceIntegrationClient instance
    """
    if 'service_integration_client' not in g:
        base_url = current_app.config.get('SERVICE_INTEGRATION_API_URL')
        timeout = current_app.config.get('API_TIMEOUT')
        g.service_integration_client = SyncServiceIntegrationClient(base_url, timeout)
    
    return g.service_integration_client

def get_tool_integration_client() -> SyncToolIntegrationClient:
    """
    Get or create a Tool Integration API client.
    
    Returns:
        SyncToolIntegrationClient instance
    """
    if 'tool_integration_client' not in g:
        base_url = current_app.config.get('TOOL_INTEGRATION_API_URL')
        timeout = current_app.config.get('API_TIMEOUT')
        g.tool_integration_client = SyncToolIntegrationClient(base_url, timeout)
    
    return g.tool_integration_client

def close_api_clients(e=None) -> None:
    """
    Close API client connections.
    
    Args:
        e: Exception that triggered the teardown (if any)
    """
    # Close Agent Orchestrator client
    agent_orchestrator_client = g.pop('agent_orchestrator_client', None)
    if agent_orchestrator_client is not None and hasattr(agent_orchestrator_client, 'session'):
        agent_orchestrator_client.session.close()
    
    # Close Project Coordinator client
    project_coordinator_client = g.pop('project_coordinator_client', None)
    if project_coordinator_client is not None and hasattr(project_coordinator_client, 'session'):
        project_coordinator_client.session.close()
    
    # Close Model Orchestration client
    model_orchestration_client = g.pop('model_orchestration_client', None)
    if model_orchestration_client is not None and hasattr(model_orchestration_client, 'session'):
        model_orchestration_client.session.close()
    
    # Close Planning System client
    planning_system_client = g.pop('planning_system_client', None)
    if planning_system_client is not None and hasattr(planning_system_client, 'session'):
        planning_system_client.session.close()
    
    # Close Service Integration client
    service_integration_client = g.pop('service_integration_client', None)
    if service_integration_client is not None and hasattr(service_integration_client, 'session'):
        service_integration_client.session.close()
    
    # Close Tool Integration client
    tool_integration_client = g.pop('tool_integration_client', None)
    if tool_integration_client is not None and hasattr(tool_integration_client, 'session'):
        tool_integration_client.session.close()
