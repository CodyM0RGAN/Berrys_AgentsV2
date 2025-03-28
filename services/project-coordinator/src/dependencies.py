"""
Dependency injection module for the Project Coordinator service.

This module defines dependencies that can be injected into FastAPI route handlers.
"""
import logging
from typing import Generator, Callable
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import redis
from fastapi import Depends

from .config import Settings, get_settings
from .repositories.base import BaseRepository
from .repositories.project import ProjectRepository
from .services.project_facade import ProjectFacade
from .services.lifecycle.manager import LifecycleManager
from .services.progress.tracker import ProgressTracker
from .services.resources.manager import ResourceManager
from .services.analytics.engine import AnalyticsEngine
from .services.artifacts.store import ArtifactStore
from .services.model_orchestrator.client import ModelOrchestratorClient


# Database setup
@lru_cache
def get_engine(settings: Settings = Depends(get_settings)):
    """Get SQLAlchemy engine instance."""
    return create_engine(settings.database_url)


@lru_cache
def get_session_factory(engine=Depends(get_engine)):
    """Get SQLAlchemy session factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db(session_factory=Depends(get_session_factory)) -> Generator[Session, None, None]:
    """
    Get a SQLAlchemy session.
    
    Yields:
        Session: SQLAlchemy session
        
    Notes:
        This function is used as a dependency in FastAPI route handlers.
        It creates a new session for each request and closes it when the request is done.
    """
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


# Redis setup
@lru_cache
def get_redis_client(settings: Settings = Depends(get_settings)):
    """Get Redis client instance."""
    return redis.Redis.from_url(settings.redis_url)


# Repositories
def get_project_repository(db: Session = Depends(get_db)) -> ProjectRepository:
    """Get ProjectRepository instance."""
    return ProjectRepository(db)


# Services
def get_lifecycle_manager(
    project_repo: ProjectRepository = Depends(get_project_repository),
    settings: Settings = Depends(get_settings)
) -> LifecycleManager:
    """Get LifecycleManager instance."""
    return LifecycleManager(
        project_repo=project_repo,
        settings=settings
    )


def get_progress_tracker(
    project_repo: ProjectRepository = Depends(get_project_repository),
    settings: Settings = Depends(get_settings)
) -> ProgressTracker:
    """Get ProgressTracker instance."""
    return ProgressTracker(
        project_repo=project_repo,
        settings=settings
    )


def get_resource_manager(
    project_repo: ProjectRepository = Depends(get_project_repository),
    settings: Settings = Depends(get_settings)
) -> ResourceManager:
    """Get ResourceManager instance."""
    return ResourceManager(
        project_repo=project_repo,
        settings=settings
    )


def get_analytics_engine(
    project_repo: ProjectRepository = Depends(get_project_repository),
    settings: Settings = Depends(get_settings)
) -> AnalyticsEngine:
    """Get AnalyticsEngine instance."""
    return AnalyticsEngine(
        project_repo=project_repo,
        settings=settings
    )


def get_artifact_store(
    project_repo: ProjectRepository = Depends(get_project_repository),
    settings: Settings = Depends(get_settings)
) -> ArtifactStore:
    """Get ArtifactStore instance."""
    return ArtifactStore(
        project_repo=project_repo,
        settings=settings
    )


# Model Orchestrator Client
def get_model_orchestrator_client(settings: Settings = Depends(get_settings)):
    """Get ModelOrchestratorClient instance."""
    return ModelOrchestratorClient(
        base_url=settings.model_orchestration_url,
        api_key=settings.model_orchestration_api_key
    )


# Facade Service
def get_project_facade(
    project_repo: ProjectRepository = Depends(get_project_repository),
    lifecycle_manager: LifecycleManager = Depends(get_lifecycle_manager),
    progress_tracker: ProgressTracker = Depends(get_progress_tracker),
    resource_manager: ResourceManager = Depends(get_resource_manager),
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine),
    artifact_store: ArtifactStore = Depends(get_artifact_store),
    settings: Settings = Depends(get_settings)
) -> ProjectFacade:
    """Get ProjectFacade instance."""
    return ProjectFacade(
        project_repo=project_repo,
        lifecycle_manager=lifecycle_manager,
        progress_tracker=progress_tracker,
        resource_manager=resource_manager,
        analytics_engine=analytics_engine,
        artifact_store=artifact_store,
        settings=settings
    )
