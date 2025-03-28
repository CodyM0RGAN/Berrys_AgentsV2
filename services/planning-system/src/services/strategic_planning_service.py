"""
Strategic Planning Service for the Planning System.

This module implements the strategic planning service with high-level planning capabilities,
providing advanced planning features for strategic plans.
"""

import logging
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from shared.utils.src.messaging import EventBus

from ..config import PlanningSystemConfig as Settings
from ..models.api import (
    StrategicPlanCreate,
    StrategicPlanUpdate,
    StrategicPlanResponse,
    OptimizationRequest,
    OptimizationResultResponse,
    ForecastRequest,
    TimelineForecastResponse,
    BottleneckAnalysisResponse
)
from ..exceptions import (
    PlanNotFoundError,
    PlanValidationError,
    TemplateNotFoundError,
    MethodologyNotFoundError,
    OptimizationError,
    ForecastingError
)
from .repository import PlanningRepository
from .plan_template_service import PlanTemplateService
from .planning_methodology_service import PlanningMethodologyService

from .strategic_planning.helper_service import HelperService
from .strategic_planning.plan_creation_service import PlanCreationService
from .strategic_planning.plan_generation_service import PlanGenerationService
from .strategic_planning.plan_optimization_service import PlanOptimizationService
from .strategic_planning.plan_forecasting_service import PlanForecastingService
from .strategic_planning.methodology_application_service import MethodologyApplicationService

logger = logging.getLogger(__name__)

class StrategicPlanningService:
    """
    Strategic planning service with high-level planning capabilities.
    
    This service extends the basic strategic planning functionality with
    advanced features for high-level planning, including template-based planning,
    methodology-driven planning, and AI-assisted planning.
    """
    
    def __init__(
        self,
        repository: PlanningRepository,
        template_service: PlanTemplateService,
        methodology_service: PlanningMethodologyService,
        event_bus: EventBus,
    ):
        """
        Initialize the strategic planning service.
        
        Args:
            repository: Planning repository
            template_service: Plan template service
            methodology_service: Planning methodology service
            event_bus: Event bus
        """
        self.repository = repository
        self.template_service = template_service
        self.methodology_service = methodology_service
        self.event_bus = event_bus
        
        # Initialize helper service
        self.helper_service = HelperService(repository)
        
        # Initialize methodology application service
        self.methodology_application_service = MethodologyApplicationService(repository)
        
        # Initialize specialized services
        self.plan_creation_service = PlanCreationService(
            repository,
            template_service,
            methodology_service,
            self.methodology_application_service,
            self.helper_service,
            event_bus
        )
        
        self.plan_generation_service = PlanGenerationService(
            repository,
            self.helper_service,
            event_bus
        )
        
        self.plan_optimization_service = PlanOptimizationService(
            repository,
            self.helper_service,
            event_bus
        )
        
        self.plan_forecasting_service = PlanForecastingService(
            repository,
            self.helper_service,
            event_bus
        )
        
        logger.info("Strategic Planning Service initialized")
    
    async def create_plan_from_template(
        self,
        project_id: UUID,
        template_id: UUID,
        plan_name: str,
        plan_description: Optional[str] = None,
        start_date: Optional[datetime] = None,
        customization_options: Optional[Dict[str, Any]] = None
    ) -> StrategicPlanResponse:
        """
        Create a strategic plan from a template.
        
        Args:
            project_id: Project ID
            template_id: Template ID
            plan_name: Plan name
            plan_description: Optional plan description
            start_date: Optional start date (defaults to current date)
            customization_options: Optional customization options
            
        Returns:
            StrategicPlanResponse: Created plan
            
        Raises:
            TemplateNotFoundError: If template not found
            PlanValidationError: If plan data is invalid
        """
        return await self.plan_creation_service.create_plan_from_template(
            project_id,
            template_id,
            plan_name,
            plan_description,
            start_date,
            customization_options
        )
    
    async def create_plan_with_methodology(
        self,
        project_id: UUID,
        methodology_id: UUID,
        plan_name: str,
        plan_description: Optional[str] = None,
        objectives: Dict[str, Any] = None,
        constraints: Dict[str, Any] = None,
        start_date: Optional[datetime] = None
    ) -> StrategicPlanResponse:
        """
        Create a strategic plan using a planning methodology.
        
        Args:
            project_id: Project ID
            methodology_id: Methodology ID
            plan_name: Plan name
            plan_description: Optional plan description
            objectives: Optional plan objectives
            constraints: Optional plan constraints
            start_date: Optional start date (defaults to current date)
            
        Returns:
            StrategicPlanResponse: Created plan
            
        Raises:
            MethodologyNotFoundError: If methodology not found
            PlanValidationError: If plan data is invalid
        """
        return await self.plan_creation_service.create_plan_with_methodology(
            project_id,
            methodology_id,
            plan_name,
            plan_description,
            objectives,
            constraints,
            start_date
        )
    
    async def generate_plan_structure(
        self,
        plan_id: UUID,
        generation_options: Dict[str, Any] = None
    ) -> StrategicPlanResponse:
        """
        Generate plan structure using AI assistance.
        
        Args:
            plan_id: Plan ID
            generation_options: Optional generation options
            
        Returns:
            StrategicPlanResponse: Updated plan
            
        Raises:
            PlanNotFoundError: If plan not found
            PlanValidationError: If plan is not in DRAFT status
        """
        return await self.plan_generation_service.generate_plan_structure(
            plan_id,
            generation_options
        )
    
    async def optimize_plan(
        self,
        optimization_request: OptimizationRequest
    ) -> OptimizationResultResponse:
        """
        Optimize a strategic plan.
        
        Args:
            optimization_request: Optimization request
            
        Returns:
            OptimizationResultResponse: Optimization result
            
        Raises:
            PlanNotFoundError: If plan not found
            OptimizationError: If optimization fails
        """
        return await self.plan_optimization_service.optimize_plan(
            optimization_request
        )
    
    async def forecast_timeline(
        self,
        forecast_request: ForecastRequest
    ) -> TimelineForecastResponse:
        """
        Generate a timeline forecast for a strategic plan.
        
        Args:
            forecast_request: Forecast request
            
        Returns:
            TimelineForecastResponse: Timeline forecast
            
        Raises:
            PlanNotFoundError: If plan not found
            ForecastingError: If forecasting fails
        """
        return await self.plan_forecasting_service.forecast_timeline(
            forecast_request
        )
    
    async def analyze_bottlenecks(
        self,
        plan_id: UUID
    ) -> BottleneckAnalysisResponse:
        """
        Analyze bottlenecks in a strategic plan.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            BottleneckAnalysisResponse: Bottleneck analysis
            
        Raises:
            PlanNotFoundError: If plan not found
            ForecastingError: If analysis fails
        """
        return await self.plan_forecasting_service.analyze_bottlenecks(
            plan_id
        )
