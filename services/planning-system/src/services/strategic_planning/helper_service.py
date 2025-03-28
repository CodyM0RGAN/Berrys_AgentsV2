"""
Helper Service for Strategic Planning.

This module provides helper methods for the strategic planning service.
"""

import logging
from typing import Dict, Any
from uuid import UUID
from datetime import datetime

from ..repository import PlanningRepository

logger = logging.getLogger(__name__)

class HelperService:
    """
    Helper service for strategic planning.
    
    This service provides helper methods for the strategic planning service,
    such as converting models to response models.
    """
    
    def __init__(self, repository: PlanningRepository):
        """
        Initialize the helper service.
        
        Args:
            repository: Planning repository
        """
        self.repository = repository
        logger.info("Helper Service initialized")
    
    async def to_plan_response_model(self, plan) -> Any:
        """
        Convert a plan model to a response model.
        
        Args:
            plan: Strategic plan model
            
        Returns:
            StrategicPlanResponse: Plan response model
        """
        # Count related entities
        phase_count = await self.repository.count_plan_phases(plan.id)
        milestone_count = await self.repository.count_plan_milestones(plan.id)
        task_count = await self.repository.count_plan_tasks(plan.id)
        
        # Calculate progress
        progress = await self.repository.calculate_plan_progress(plan.id)
        
        # Get methodology and template names if applicable
        methodology_name = None
        if plan.methodology_id:
            methodology = await self.repository.get_methodology_by_id(plan.methodology_id)
            if methodology:
                methodology_name = methodology.name
        
        template_name = None
        if plan.template_id:
            template = await self.repository.get_template_by_id(plan.template_id)
            if template:
                template_name = template.name
        
        # Create response model
        from ...models.api import StrategicPlanResponse
        
        return StrategicPlanResponse(
            data={
                "id": plan.id,
                "name": plan.name,
                "description": plan.description,
                "project_id": plan.project_id,
                "methodology_id": plan.methodology_id,
                "template_id": plan.template_id,
                "constraints": plan.constraints,
                "objectives": plan.objectives,
                "status": plan.status,
                "created_at": plan.created_at,
                "updated_at": plan.updated_at,
                "phase_count": phase_count,
                "milestone_count": milestone_count,
                "task_count": task_count,
                "progress": progress,
                "methodology_name": methodology_name,
                "template_name": template_name,
            },
            message="Strategic plan retrieved successfully",
            success=True
        )
    
    async def publish_plan_created_from_template_event(self, plan, template, event_bus) -> None:
        """
        Publish plan created from template event.
        
        Args:
            plan: Created plan
            template: Source template
            event_bus: Event bus
        """
        event_data = {
            "plan_id": str(plan.id),
            "name": plan.name,
            "project_id": str(plan.project_id),
            "template_id": str(template.id),
            "template_name": template.name,
            "created_at": plan.created_at.isoformat(),
        }
        
        await event_bus.publish("plan.created.from_template", event_data)
    
    async def publish_plan_created_with_methodology_event(self, plan, methodology, event_bus) -> None:
        """
        Publish plan created with methodology event.
        
        Args:
            plan: Created plan
            methodology: Source methodology
            event_bus: Event bus
        """
        event_data = {
            "plan_id": str(plan.id),
            "name": plan.name,
            "project_id": str(plan.project_id),
            "methodology_id": str(methodology.id),
            "methodology_name": methodology.name,
            "methodology_type": methodology.methodology_type,
            "created_at": plan.created_at.isoformat(),
        }
        
        await event_bus.publish("plan.created.with_methodology", event_data)
    
    async def publish_plan_structure_generated_event(self, plan, event_bus) -> None:
        """
        Publish plan structure generated event.
        
        Args:
            plan: Updated plan
            event_bus: Event bus
        """
        event_data = {
            "plan_id": str(plan.id),
            "name": plan.name,
            "project_id": str(plan.project_id),
            "updated_at": plan.updated_at.isoformat(),
        }
        
        await event_bus.publish("plan.structure.generated", event_data)
    
    async def publish_plan_optimized_event(self, plan, optimization_result, event_bus) -> None:
        """
        Publish plan optimized event.
        
        Args:
            plan: Optimized plan
            optimization_result: Optimization result
            event_bus: Event bus
        """
        event_data = {
            "plan_id": str(plan.id),
            "name": plan.name,
            "project_id": str(plan.project_id),
            "optimization_target": str(optimization_result.data.optimization_target),
            "status": optimization_result.data.status,
            "metrics": optimization_result.data.metrics,
            "updated_at": datetime.now().isoformat(),
        }
        
        await event_bus.publish("plan.optimized", event_data)
    
    async def publish_timeline_forecasted_event(self, plan, forecast, event_bus) -> None:
        """
        Publish timeline forecasted event.
        
        Args:
            plan: Plan
            forecast: Timeline forecast
            event_bus: Event bus
        """
        event_data = {
            "plan_id": str(plan.id),
            "name": plan.name,
            "project_id": str(plan.project_id),
            "expected_completion": forecast.data.expected_completion.isoformat(),
            "confidence_interval": forecast.data.confidence_interval,
            "generated_at": forecast.data.generated_at.isoformat(),
        }
        
        await event_bus.publish("plan.timeline.forecasted", event_data)
    
    async def publish_bottlenecks_analyzed_event(self, plan, analysis, event_bus) -> None:
        """
        Publish bottlenecks analyzed event.
        
        Args:
            plan: Plan
            analysis: Bottleneck analysis
            event_bus: Event bus
        """
        event_data = {
            "plan_id": str(plan.id),
            "name": plan.name,
            "project_id": str(plan.project_id),
            "bottleneck_count": len(analysis.data.bottlenecks),
            "recommendation_count": len(analysis.data.recommendations),
            "generated_at": analysis.data.generated_at.isoformat(),
        }
        
        await event_bus.publish("plan.bottlenecks.analyzed", event_data)
