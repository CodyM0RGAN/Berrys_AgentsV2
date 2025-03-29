"""
Model registry for mapping between SQLAlchemy and Pydantic models.

This module provides utilities for registering and retrieving model mappings,
as well as converting between SQLAlchemy and Pydantic models.
"""

from typing import Dict, List, Optional, Type, Any, Tuple
import importlib
import inspect
import logging

from pydantic import BaseModel
from sqlalchemy.ext.declarative import DeclarativeMeta

from shared.models.src.base import ModelRegistry, register_models

logger = logging.getLogger(__name__)

# Dictionary of service names to module paths
SERVICE_MODULES = {
    'web_dashboard': {
        'sqlalchemy': None,  # Disable SQLAlchemy import for web_dashboard
        'pydantic': 'shared.models.src'
    },
    'project_coordinator': {
        'sqlalchemy': 'services.project_coordinator.src.models.internal',  # Use absolute import path
        'pydantic': 'shared.models.src'
    },
    'agent_orchestrator': {
        'sqlalchemy': 'services.agent_orchestrator.src.models.internal',  # Use absolute import path
        'pydantic': 'shared.models.src'
    },
    'model_orchestration': {
        'sqlalchemy': 'services.model_orchestration.src.models.internal',  # Use absolute import path
        'pydantic': 'shared.models.src'
    },
    'planning_system': {
        'sqlalchemy': 'services.planning_system.src.models.internal',  # Use absolute import path
        'pydantic': 'shared.models.src'
    },
    'tool_integration': {
        'sqlalchemy': 'services.tool_integration.src.models.internal',  # Use absolute import path
        'pydantic': 'shared.models.src'
    }
}

# Dictionary of entity names to model types
ENTITY_MODELS = {
    'project': {
        'default': 'Project',
        'create': 'ProjectCreate',
        'update': 'ProjectUpdate',
        'summary': 'ProjectSummary'
    },
    'agent': {
        'default': 'Agent',
        'create': 'AgentCreate',
        'update': 'AgentUpdate',
        'summary': 'AgentSummary'
    },
    'task': {
        'default': 'Task',
        'create': 'TaskCreate',
        'update': 'TaskUpdate',
        'summary': 'TaskSummary'
    },
    'tool': {
        'default': 'Tool',
        'create': 'ToolCreate',
        'update': 'ToolUpdate',
        'summary': 'ToolSummary'
    },
    'model': {
        'default': 'Model',
        'create': 'ModelCreate',
        'update': 'ModelUpdate',
        'summary': 'ModelSummary'
    },
    'user': {
        'default': 'User',
        'create': 'UserCreate',
        'update': 'UserUpdate',
        'summary': 'UserSummary'
    },
    'audit': {
        'default': 'AuditLog',
        'summary': 'AuditSummary'
    },
    'human': {
        'default': 'HumanInteraction'
    }
}


def register_all_models():
    """
    Register all model mappings between SQLAlchemy and Pydantic models.
    
    This function imports all model modules and registers the mappings
    between SQLAlchemy and Pydantic models.
    """
    for service_name, modules in SERVICE_MODULES.items():
        sqlalchemy_module_path = modules['sqlalchemy']
        pydantic_module_path = modules['pydantic']
        
        # Skip if SQLAlchemy module path is None
        if sqlalchemy_module_path is None:
            logger.info(f"Skipping SQLAlchemy import for {service_name}")
            continue
        
        try:
            # Import SQLAlchemy models
            sqlalchemy_module = importlib.import_module(sqlalchemy_module_path)
            
            # Get all SQLAlchemy model classes
            sqlalchemy_models = {}
            for name, obj in inspect.getmembers(sqlalchemy_module):
                if isinstance(obj, type) and hasattr(obj, '__tablename__'):
                    sqlalchemy_models[name.lower()] = obj
            
            # Import Pydantic models for each entity
            for entity_name, model_types in ENTITY_MODELS.items():
                try:
                    # Try to import the entity-specific module first
                    try:
                        pydantic_entity_module = importlib.import_module(f"{pydantic_module_path}.{entity_name}")
                    except ImportError:
                        # Fall back to the main module
                        pydantic_entity_module = importlib.import_module(pydantic_module_path)
                    
                    # Get SQLAlchemy model for this entity
                    sqlalchemy_model = sqlalchemy_models.get(entity_name)
                    if not sqlalchemy_model:
                        continue
                    
                    # Register mappings for each model type
                    for model_type, model_name in model_types.items():
                        try:
                            pydantic_model = getattr(pydantic_entity_module, model_name)
                            register_models(sqlalchemy_model, pydantic_model, model_type)
                            logger.info(f"Registered mapping: {sqlalchemy_model.__name__} -> {pydantic_model.__name__} ({model_type})")
                        except AttributeError:
                            logger.warning(f"Pydantic model {model_name} not found in {pydantic_entity_module.__name__}")
                
                except ImportError as e:
                    logger.warning(f"Could not import Pydantic module for {entity_name}: {e}")
        
        except ImportError as e:
            logger.warning(f"Could not import SQLAlchemy module for {service_name}: {e}")


def get_model_mappings() -> Dict[str, Dict[str, Dict[str, Tuple[Type, Type]]]]:
    """
    Get all registered model mappings.
    
    Returns:
        Dict[str, Dict[str, Dict[str, Tuple[Type, Type]]]]: Dictionary of service -> entity -> model_type -> (SQLAlchemy, Pydantic)
    """
    mappings = {}
    
    for service_name in SERVICE_MODULES.keys():
        mappings[service_name] = {}
        
        for entity_name in ENTITY_MODELS.keys():
            mappings[service_name][entity_name] = {}
            
            for model_type in ENTITY_MODELS[entity_name].keys():
                sqlalchemy_model = None
                pydantic_model = None
                
                # Find the SQLAlchemy model
                sqlalchemy_module_path = SERVICE_MODULES[service_name]['sqlalchemy']
                if sqlalchemy_module_path is not None:
                    try:
                        sqlalchemy_module = importlib.import_module(sqlalchemy_module_path)
                        for name, obj in inspect.getmembers(sqlalchemy_module):
                            if isinstance(obj, type) and hasattr(obj, '__tablename__') and obj.__tablename__ == entity_name:
                                sqlalchemy_model = obj
                                break
                    except ImportError:
                        pass
                
                # Find the Pydantic model
                try:
                    pydantic_module = importlib.import_module(SERVICE_MODULES[service_name]['pydantic'])
                    pydantic_model_name = ENTITY_MODELS[entity_name][model_type]
                    pydantic_model = getattr(pydantic_module, pydantic_model_name, None)
                except (ImportError, AttributeError):
                    pass
                
                if sqlalchemy_model and pydantic_model:
                    mappings[service_name][entity_name][model_type] = (sqlalchemy_model, pydantic_model)
    
    return mappings


def get_model_diagram() -> str:
    """
    Generate a Mermaid diagram of the model mappings.
    
    Returns:
        str: Mermaid diagram code
    """
    mappings = get_model_mappings()
    
    diagram = ["```mermaid", "classDiagram"]
    
    # Add SQLAlchemy models
    for service_name, entities in mappings.items():
        for entity_name, model_types in entities.items():
            for model_type, (sqlalchemy_model, pydantic_model) in model_types.items():
                if sqlalchemy_model and pydantic_model:
                    diagram.append(f"    class {sqlalchemy_model.__name__}")
                    diagram.append(f"    class {pydantic_model.__name__}")
                    diagram.append(f"    {sqlalchemy_model.__name__} <--> {pydantic_model.__name__} : {model_type}")
    
    diagram.append("```")
    
    return "\n".join(diagram)


# Register all models when this module is imported
register_all_models()
