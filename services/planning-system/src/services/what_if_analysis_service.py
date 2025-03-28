"""
What-If Analysis Service for the Planning System.

This module implements the what-if analysis service, which provides
functionality for scenario modeling and impact analysis.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple, Union
from uuid import UUID
from datetime import datetime, timedelta
import copy

from shared.utils.src.messaging import EventBus

from ..models.api import (
    WhatIfScenarioCreate,
    WhatIfScenarioUpdate,
    WhatIfScenarioResponse,
    WhatIfAnalysisResult,
    TimelineForecast,
    PaginatedResponse
)
from ..exceptions import (
    ScenarioNotFoundError,
    ForecastingError
)
from .repository import PlanningRepository
from .forecaster import ProjectForecaster
from .base import BasePlannerComponent

logger = logging.getLogger(__name__)

class WhatIfAnalysisService(BasePlannerComponent):
    """
    What-If Analysis Service.
    
    This service provides functionality for scenario modeling and impact analysis,
    allowing users to explore different project scenarios and their effects.
    """
    
    def __init__(
        self,
        repository: PlanningRepository,
        event_bus: EventBus,
        forecaster: ProjectForecaster,
    ):
        """
        Initialize the what-if analysis service.
        
        Args:
            repository: Planning repository
            event_bus: Event bus
            forecaster: Project forecaster component
        """
        super().__init__(repository, event_bus, "WhatIfAnalysisService")
        self.forecaster = forecaster
    
    async def create_scenario(self, scenario_data: WhatIfScenarioCreate) -> WhatIfScenarioResponse:
        """
        Create a new what-if scenario.
        
        Args:
            scenario_data: Scenario data
            
        Returns:
            WhatIfScenarioResponse: Created scenario
            
        Raises:
            Exception: If scenario creation fails
        """
        await self._log_operation("Creating", "what-if scenario", entity_name=scenario_data.name)
        
        # Validate plan exists
        plan = await self.repository.get_plan_by_id(scenario_data.plan_id)
        if not plan:
            await self._handle_not_found_error("plan", scenario_data.plan_id)
        
        # Convert to dict for repository
        scenario_dict = scenario_data.model_dump()
        
        # Create scenario in repository
        scenario = await self.repository.create_what_if_scenario(scenario_dict)
        
        # Publish event
        await self._publish_event("what_if_scenario.created", scenario)
        
        # Convert to response model
        return await self._to_response_model(scenario)
    
    async def get_scenario(self, scenario_id: UUID) -> WhatIfScenarioResponse:
        """
        Get a what-if scenario by ID.
        
        Args:
            scenario_id: Scenario ID
            
        Returns:
            WhatIfScenarioResponse: Scenario data
            
        Raises:
            ScenarioNotFoundError: If scenario not found
        """
        await self._log_operation("Getting", "what-if scenario", entity_id=scenario_id)
        
        # Get scenario from repository
        scenario = await self.repository.get_what_if_scenario_by_id(scenario_id)
        
        if not scenario:
            await self._handle_not_found_error("what-if scenario", scenario_id, ScenarioNotFoundError)
        
        # Convert to response model
        return await self._to_response_model(scenario)
    
    async def list_scenarios(
        self,
        plan_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """
        List what-if scenarios for a plan with pagination.
        
        Args:
            plan_id: Plan ID
            page: Page number
            page_size: Items per page
            
        Returns:
            PaginatedResponse: Paginated list of scenarios
        """
        await self._log_operation("Listing", "what-if scenarios", entity_name=f"for plan {plan_id}")
        
        # Build filters
        filters = {"plan_id": plan_id}
        
        # Get scenarios from repository
        scenarios, total = await self.repository.list_what_if_scenarios(
            filters=filters,
            pagination={"page": page, "page_size": page_size}
        )
        
        # Convert to response models
        scenario_responses = [await self._to_response_model(scenario) for scenario in scenarios]
        
        # Build paginated response
        return PaginatedResponse(
            items=scenario_responses,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        )
    
    async def update_scenario(
        self,
        scenario_id: UUID,
        scenario_data: WhatIfScenarioUpdate
    ) -> WhatIfScenarioResponse:
        """
        Update a what-if scenario.
        
        Args:
            scenario_id: Scenario ID
            scenario_data: Scenario data to update
            
        Returns:
            WhatIfScenarioResponse: Updated scenario
            
        Raises:
            ScenarioNotFoundError: If scenario not found
        """
        await self._log_operation("Updating", "what-if scenario", entity_id=scenario_id)
        
        # Get existing scenario
        scenario = await self.repository.get_what_if_scenario_by_id(scenario_id)
        if not scenario:
            await self._handle_not_found_error("what-if scenario", scenario_id, ScenarioNotFoundError)
        
        # Convert to dict for repository
        update_dict = scenario_data.model_dump(exclude_unset=True)
        
        # Update scenario in repository
        scenario = await self.repository.update_what_if_scenario(scenario_id, update_dict)
        
        if not scenario:
            await self._handle_not_found_error("what-if scenario", scenario_id, ScenarioNotFoundError)
        
        # Publish event
        await self._publish_event("what_if_scenario.updated", scenario)
        
        # Convert to response model
        return await self._to_response_model(scenario)
    
    async def delete_scenario(self, scenario_id: UUID) -> None:
        """
        Delete a what-if scenario.
        
        Args:
            scenario_id: Scenario ID
            
        Raises:
            ScenarioNotFoundError: If scenario not found
        """
        await self._log_operation("Deleting", "what-if scenario", entity_id=scenario_id)
        
        # Get scenario data for event
        scenario = await self.repository.get_what_if_scenario_by_id(scenario_id)
        
        if not scenario:
            await self._handle_not_found_error("what-if scenario", scenario_id, ScenarioNotFoundError)
        
        # Delete scenario in repository
        success = await self.repository.delete_what_if_scenario(scenario_id)
        
        if not success:
            await self._handle_not_found_error("what-if scenario", scenario_id, ScenarioNotFoundError)
        
        # Publish event
        await self._publish_event("what_if_scenario.deleted", scenario)
    
    async def run_what_if_analysis(
        self,
        scenario_id: UUID,
        confidence_interval: Optional[float] = None,
    ) -> WhatIfAnalysisResult:
        """
        Run what-if analysis for a scenario.
        
        Args:
            scenario_id: Scenario ID
            confidence_interval: Optional confidence interval (0.0-1.0)
            
        Returns:
            WhatIfAnalysisResult: Analysis result
            
        Raises:
            ScenarioNotFoundError: If scenario not found
            ForecastingError: If analysis fails
        """
        await self._log_operation("Running", "what-if analysis", entity_id=scenario_id)
        
        # Get scenario
        scenario = await self.repository.get_what_if_scenario_by_id(scenario_id)
        
        if not scenario:
            await self._handle_not_found_error("what-if scenario", scenario_id, ScenarioNotFoundError)
        
        # Get plan
        plan = await self.repository.get_plan_by_id(scenario.plan_id)
        if not plan:
            await self._handle_not_found_error("plan", scenario.plan_id)
        
        try:
            # Apply scenario modifications to create a temporary plan state
            modified_plan, modified_tasks, modified_resources = await self._apply_scenario_modifications(scenario)
            
            # Generate forecast for modified plan
            forecast = await self._generate_forecast_for_modified_plan(
                plan=modified_plan,
                tasks=modified_tasks,
                resources=modified_resources,
                confidence_interval=confidence_interval or 0.95
            )
            
            # Get baseline forecast for comparison
            baseline_forecast = await self.forecaster.get_latest_forecast(scenario.plan_id)
            
            # If no baseline forecast exists, create one
            if not baseline_forecast:
                baseline_forecast = await self.forecaster.create_forecast(
                    plan_id=scenario.plan_id,
                    confidence_interval=confidence_interval or 0.95
                )
            
            # Compare forecasts
            comparison = await self._compare_forecasts(baseline_forecast, forecast)
            
            # Create analysis result
            analysis_result = WhatIfAnalysisResult(
                scenario_id=scenario_id,
                plan_id=scenario.plan_id,
                generated_at=datetime.utcnow(),
                baseline_forecast=baseline_forecast,
                scenario_forecast=forecast,
                comparison=comparison,
                scenario_description=scenario.description,
                scenario_name=scenario.name
            )
            
            # Store analysis result
            result_dict = analysis_result.model_dump()
            stored_result = await self.repository.create_what_if_analysis_result(result_dict)
            
            # Publish event
            await self._publish_event(
                "what_if_analysis.completed", 
                stored_result,
                {"scenario_id": str(scenario_id), "plan_id": str(scenario.plan_id)}
            )
            
            return analysis_result
        
        except Exception as e:
            self.logger.error(f"What-if analysis error: {str(e)}")
            raise ForecastingError(
                message=f"Failed to run what-if analysis: {str(e)}",
                details={"scenario_id": str(scenario_id)}
            )
    
    async def compare_scenarios(
        self,
        scenario_id_1: UUID,
        scenario_id_2: UUID
    ) -> Dict[str, Any]:
        """
        Compare two what-if scenarios.
        
        Args:
            scenario_id_1: First scenario ID
            scenario_id_2: Second scenario ID
            
        Returns:
            Dict[str, Any]: Comparison results
            
        Raises:
            ScenarioNotFoundError: If scenario not found
        """
        await self._log_operation(
            "Comparing", 
            "what-if scenarios", 
            entity_name=f"between {scenario_id_1} and {scenario_id_2}"
        )
        
        # Get scenarios
        scenario1 = await self.repository.get_what_if_scenario_by_id(scenario_id_1)
        if not scenario1:
            await self._handle_not_found_error("what-if scenario", scenario_id_1, ScenarioNotFoundError)
        
        scenario2 = await self.repository.get_what_if_scenario_by_id(scenario_id_2)
        if not scenario2:
            await self._handle_not_found_error("what-if scenario", scenario_id_2, ScenarioNotFoundError)
        
        # Ensure scenarios are for the same plan
        if scenario1.plan_id != scenario2.plan_id:
            raise ForecastingError(
                message="Cannot compare scenarios for different plans",
                details={
                    "scenario1_id": str(scenario_id_1),
                    "scenario1_plan_id": str(scenario1.plan_id),
                    "scenario2_id": str(scenario_id_2),
                    "scenario2_plan_id": str(scenario2.plan_id)
                }
            )
        
        # Get latest analysis results for both scenarios
        result1 = await self.repository.get_latest_what_if_analysis_result(scenario_id_1)
        result2 = await self.repository.get_latest_what_if_analysis_result(scenario_id_2)
        
        if not result1 or not result2:
            # Run analysis for scenarios without results
            if not result1:
                result1 = await self.run_what_if_analysis(scenario_id_1)
            
            if not result2:
                result2 = await self.run_what_if_analysis(scenario_id_2)
        
        # Compare forecasts
        comparison = await self._compare_forecasts(result1.scenario_forecast, result2.scenario_forecast)
        
        # Add scenario information
        comparison["scenarios"] = {
            "scenario1": {
                "id": str(scenario_id_1),
                "name": scenario1.name,
                "description": scenario1.description
            },
            "scenario2": {
                "id": str(scenario_id_2),
                "name": scenario2.name,
                "description": scenario2.description
            }
        }
        
        # Add modification differences
        modification_diff = self._compare_scenario_modifications(scenario1, scenario2)
        comparison["modification_differences"] = modification_diff
        
        return comparison
    
    async def apply_scenario_to_plan(
        self,
        scenario_id: UUID
    ) -> Dict[str, Any]:
        """
        Apply a what-if scenario to the actual plan.
        
        Args:
            scenario_id: Scenario ID
            
        Returns:
            Dict[str, Any]: Result of applying the scenario
            
        Raises:
            ScenarioNotFoundError: If scenario not found
        """
        await self._log_operation("Applying", "what-if scenario to plan", entity_id=scenario_id)
        
        # Get scenario
        scenario = await self.repository.get_what_if_scenario_by_id(scenario_id)
        
        if not scenario:
            await self._handle_not_found_error("what-if scenario", scenario_id, ScenarioNotFoundError)
        
        # Get plan
        plan = await self.repository.get_plan_by_id(scenario.plan_id)
        if not plan:
            await self._handle_not_found_error("plan", scenario.plan_id)
        
        # Apply task modifications
        task_updates = []
        for task_mod in scenario.task_modifications:
            task_id = task_mod.get("task_id")
            if not task_id:
                continue
            
            # Get task
            task = await self.repository.get_task_by_id(UUID(task_id))
            if not task:
                continue
            
            # Apply modifications
            update_data = {}
            if "estimated_duration" in task_mod:
                update_data["estimated_duration"] = task_mod["estimated_duration"]
            if "estimated_effort" in task_mod:
                update_data["estimated_effort"] = task_mod["estimated_effort"]
            if "required_skills" in task_mod:
                update_data["required_skills"] = task_mod["required_skills"]
            if "priority" in task_mod:
                update_data["priority"] = task_mod["priority"]
            
            if update_data:
                # Update task
                updated_task = await self.repository.update_task(UUID(task_id), update_data)
                task_updates.append({
                    "task_id": task_id,
                    "name": task.name,
                    "updates": update_data
                })
        
        # Apply resource modifications
        resource_updates = []
        for resource_mod in scenario.resource_modifications:
            resource_id = resource_mod.get("resource_id")
            if not resource_id:
                continue
            
            # Get resource
            resource = await self.repository.get_resource_by_id(UUID(resource_id))
            if not resource:
                continue
            
            # Apply modifications
            update_data = {}
            if "availability" in resource_mod:
                update_data["availability"] = resource_mod["availability"]
            if "skills" in resource_mod:
                update_data["skills"] = resource_mod["skills"]
            
            if update_data:
                # Update resource
                updated_resource = await self.repository.update_resource(UUID(resource_id), update_data)
                resource_updates.append({
                    "resource_id": resource_id,
                    "name": getattr(resource, "name", f"Resource {resource_id}"),
                    "updates": update_data
                })
        
        # Apply dependency modifications
        dependency_updates = []
        for dependency_mod in scenario.dependency_modifications:
            from_task_id = dependency_mod.get("from_task_id")
            to_task_id = dependency_mod.get("to_task_id")
            if not from_task_id or not to_task_id:
                continue
            
            # Check if dependency exists
            dependency = await self.repository.get_dependency(
                from_task_id=UUID(from_task_id),
                to_task_id=UUID(to_task_id)
            )
            
            if dependency_mod.get("action") == "add" and not dependency:
                # Create dependency
                new_dependency = {
                    "from_task_id": UUID(from_task_id),
                    "to_task_id": UUID(to_task_id),
                    "dependency_type": dependency_mod.get("dependency_type", "finish_to_start"),
                    "lag": dependency_mod.get("lag", 0)
                }
                
                created_dependency = await self.repository.create_dependency(new_dependency)
                dependency_updates.append({
                    "action": "added",
                    "from_task_id": from_task_id,
                    "to_task_id": to_task_id,
                    "details": new_dependency
                })
            
            elif dependency_mod.get("action") == "remove" and dependency:
                # Delete dependency
                success = await self.repository.delete_dependency(
                    from_task_id=UUID(from_task_id),
                    to_task_id=UUID(to_task_id)
                )
                
                if success:
                    dependency_updates.append({
                        "action": "removed",
                        "from_task_id": from_task_id,
                        "to_task_id": to_task_id
                    })
            
            elif dependency_mod.get("action") == "update" and dependency:
                # Update dependency
                update_data = {}
                if "dependency_type" in dependency_mod:
                    update_data["dependency_type"] = dependency_mod["dependency_type"]
                if "lag" in dependency_mod:
                    update_data["lag"] = dependency_mod["lag"]
                
                if update_data:
                    updated_dependency = await self.repository.update_dependency(
                        from_task_id=UUID(from_task_id),
                        to_task_id=UUID(to_task_id),
                        dependency_data=update_data
                    )
                    
                    dependency_updates.append({
                        "action": "updated",
                        "from_task_id": from_task_id,
                        "to_task_id": to_task_id,
                        "updates": update_data
                    })
        
        # Create result
        result = {
            "scenario_id": str(scenario_id),
            "plan_id": str(scenario.plan_id),
            "applied_at": datetime.utcnow().isoformat(),
            "task_updates": task_updates,
            "resource_updates": resource_updates,
            "dependency_updates": dependency_updates,
            "total_updates": len(task_updates) + len(resource_updates) + len(dependency_updates)
        }
        
        # Publish event
        await self._publish_event(
            "what_if_scenario.applied", 
            result,
            {"scenario_id": str(scenario_id), "plan_id": str(scenario.plan_id)}
        )
        
        return result
    
    # Helper methods
    
    async def _to_response_model(self, scenario) -> WhatIfScenarioResponse:
        """
        Convert a scenario model to a response model.
        
        Args:
            scenario: What-if scenario model
            
        Returns:
            WhatIfScenarioResponse: Scenario response model
        """
        # Get latest analysis result
        latest_result = await self.repository.get_latest_what_if_analysis_result(scenario.id)
        
        # Convert to response model
        return WhatIfScenarioResponse(
            id=scenario.id,
            plan_id=scenario.plan_id,
            name=scenario.name,
            description=scenario.description,
            task_modifications=scenario.task_modifications,
            resource_modifications=scenario.resource_modifications,
            dependency_modifications=scenario.dependency_modifications,
            created_at=scenario.created_at,
            updated_at=scenario.updated_at,
            last_analyzed_at=latest_result.generated_at if latest_result else None,
            has_analysis_results=latest_result is not None
        )
    
    async def _apply_scenario_modifications(self, scenario) -> Tuple[Any, List[Any], List[Any]]:
        """
        Apply scenario modifications to create a temporary plan state.
        
        Args:
            scenario: What-if scenario
            
        Returns:
            Tuple[Any, List[Any], List[Any]]: Modified plan, tasks, and resources
        """
        # Get plan and related data
        plan = await self.repository.get_plan_by_id(scenario.plan_id)
        tasks = await self.repository.get_tasks_by_plan(scenario.plan_id)
        resources = await self.repository.get_resources_for_plan(scenario.plan_id)
        
        # Create deep copies to avoid modifying the original data
        modified_plan = copy.deepcopy(plan)
        modified_tasks = copy.deepcopy(tasks)
        modified_resources = copy.deepcopy(resources)
        
        # Apply task modifications
        for task_mod in scenario.task_modifications:
            task_id = task_mod.get("task_id")
            if not task_id:
                continue
            
            # Find task in modified tasks
            for i, task in enumerate(modified_tasks):
                if str(task.id) == task_id:
                    # Apply modifications
                    if "estimated_duration" in task_mod:
                        modified_tasks[i].estimated_duration = task_mod["estimated_duration"]
                    if "estimated_effort" in task_mod:
                        modified_tasks[i].estimated_effort = task_mod["estimated_effort"]
                    if "required_skills" in task_mod:
                        modified_tasks[i].required_skills = task_mod["required_skills"]
                    if "priority" in task_mod:
                        modified_tasks[i].priority = task_mod["priority"]
                    break
        
        # Apply resource modifications
        for resource_mod in scenario.resource_modifications:
            resource_id = resource_mod.get("resource_id")
            if not resource_id:
                continue
            
            # Find resource in modified resources
            for i, resource in enumerate(modified_resources):
                if str(resource.id) == resource_id:
                    # Apply modifications
                    if "availability" in resource_mod:
                        modified_resources[i].availability = resource_mod["availability"]
                    if "skills" in resource_mod:
                        modified_resources[i].skills = resource_mod["skills"]
                    break
        
        return modified_plan, modified_tasks, modified_resources
    
    async def _generate_forecast_for_modified_plan(
        self,
        plan: Any,
        tasks: List[Any],
        resources: List[Any],
        confidence_interval: float
    ) -> TimelineForecast:
        """
        Generate a forecast for a modified plan.
        
        Args:
            plan: Modified plan
            tasks: Modified tasks
            resources: Modified resources
            confidence_interval: Confidence interval
            
        Returns:
            TimelineForecast: Generated forecast
        """
        # Get dependencies
        dependencies = await self.repository.get_all_dependencies_for_plan(plan.id)
        
        # Generate timeline
        timeline_points = await self.forecaster._generate_timeline(
            plan=plan,
            tasks=tasks,
            dependencies=dependencies,
            confidence_interval=confidence_interval,
            time_unit="day"
        )
        
        # Calculate completion dates
        completion_dates = await self.forecaster._calculate_completion_dates(
            timeline_points=timeline_points,
            confidence_interval=confidence_interval
        )
        
        # Create forecast
        forecast = TimelineForecast(
            plan_id=plan.id,
            generated_at=datetime.utcnow(),
            confidence_interval=confidence_interval,
            timeline=timeline_points,
            expected_completion=completion_dates["expected"],
            best_case_completion=completion_dates["best_case"],
            worst_case_completion=completion_dates["worst_case"]
        )
        
        return forecast
    
    async def _compare_forecasts(
        self,
        forecast1: TimelineForecast,
        forecast2: TimelineForecast
    ) -> Dict[str, Any]:
        """
        Compare two forecasts.
        
        Args:
            forecast1: First forecast
            forecast2: Second forecast
            
        Returns:
            Dict[str, Any]: Comparison results
        """
        # Compare dates
        completion_diff = (forecast2.expected_completion - forecast1.expected_completion).days
        best_case_diff = (forecast2.best_case_completion - forecast1.best_case_completion).days
        worst_case_diff = (forecast2.worst_case_completion - forecast1.worst_case_completion).days
        
        # Calculate trends
        if completion_diff > 0:
            trend = "delay"
        elif completion_diff < 0:
            trend = "acceleration"
        else:
            trend = "stable"
        
        # Create comparison result
        comparison = {
            "completion_difference_days": completion_diff,
            "best_case_difference_days": best_case_diff,
            "worst_case_difference_days": worst_case_diff,
            "trend": trend,
            "percentage_change": (completion_diff / (forecast1.expected_completion - forecast1.generated_at).days) * 100 if (forecast1.expected_completion - forecast1.generated_at).days > 0 else 0,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return comparison
    
    def _compare_scenario_modifications(
        self,
        scenario1: Any,
        scenario2: Any
    ) -> Dict[str, Any]:
        """
        Compare modifications between two scenarios.
        
        Args:
            scenario1: First scenario
            scenario2: Second scenario
            
        Returns:
            Dict[str, Any]: Modification differences
        """
        # Compare task modifications
        task_diffs = []
        
        # Create dictionaries for easier comparison
        task_mods1 = {mod.get("task_id"): mod for mod in scenario1.task_modifications if "task_id" in mod}
        task_mods2 = {mod.get("task_id"): mod for mod in scenario2.task_modifications if "task_id" in mod}
        
        # Find all task IDs in either scenario
        all_task_ids = set(task_mods1.keys()) | set(task_mods2.keys())
        
        for task_id in all_task_ids:
            mod1 = task_mods1.get(task_id, {})
            mod2 = task_mods2.get(task_id, {})
            
            if task_id in task_mods1 and task_id in task_mods2:
                # Task modified in both scenarios
                field_diffs = {}
                
                for field in ["estimated_duration", "estimated_effort", "required_skills", "priority"]:
                    if field in mod1 and field in mod2 and mod1[field] != mod2[field]:
                        field_diffs[field] = {
                            "scenario1": mod1[field],
                            "scenario2": mod2[field]
                        }
                
                if field_diffs:
                    task_diffs.append({
                        "task_id": task_id,
                        "in_both_scenarios": True,
                        "differences": field_diffs
                    })
            
            elif task_id in task_mods1:
                # Task only in scenario1
                task_diffs.append({
                    "task_id": task_id,
                    "only_in_scenario1": True,
                    "modifications": mod1
                })
            
            else:
                # Task only in scenario2
                task_diffs.append({
                    "task_id": task_id,
                    "only_in_scenario2": True,
                    "modifications": mod2
                })
        
        # Compare resource modifications (similar approach)
        resource_diffs = []
        
        resource_mods1 = {mod.get("resource_id"): mod for mod in scenario1.resource_modifications if "resource_id" in mod}
        resource_mods2 = {mod.get("resource_id"): mod for mod in scenario2.resource_modifications if "resource_id" in mod}
        
        all_resource_ids = set(resource_mods1.keys()) | set(resource_mods2.keys())
        
        for resource_id in all_resource_ids:
            mod1 = resource_mods1.get(resource_id, {})
            mod2 = resource_mods2.get(resource_id, {})
            
            if resource_id in resource_mods1 and resource_id in resource_mods2:
                # Resource modified in both scenarios
                field_diffs = {}
                
                for field in ["availability", "skills"]:
                    if field in mod1 and field in mod2 and mod1[field] != mod2[field]:
                        field_diffs[field] = {
                            "scenario1": mod1[field],
                            "scenario2": mod2[field]
                        }
                
                if field_diffs:
                    resource_diffs.append({
                        "resource_id": resource_id,
                        "in_both_scenarios": True,
                        "differences": field_diffs
                    })
            
            elif resource_id in resource_mods1:
                # Resource only in scenario1
                resource_diffs.append({
                    "resource_id": resource_id,
                    "only_in_scenario1": True,
                    "modifications": mod1
                })
            
            else:
                # Resource only in scenario2
                resource_diffs.append({
                    "resource_id": resource_id,
                    "only_in_scenario2": True,
                    "modifications": mod2
                })
        
        # Compare dependency modifications
        dependency_diffs = []
        
        # Create a unique key for each dependency
        def dep_key(dep):
            return f"{dep.get('from_task_id')}_{dep.get('to_task_id')}"
        
        dep_mods1 = {dep_key(mod): mod for mod in scenario1.dependency_modifications 
                    if "from_task_id" in mod and "to_task_id" in mod}
        dep_mods2 = {dep_key(mod): mod for mod in scenario2.dependency_modifications
                    if "from_task_id" in mod and "to_task_id" in mod}
        
        # Find all dependency keys in either scenario
        all_dep_keys = set(dep_mods1.keys()) | set(dep_mods2.keys())
        
        for key in all_dep_keys:
            mod1 = dep_mods1.get(key, {})
            mod2 = dep_mods2.get(key, {})
            
            if key in dep_mods1 and key in dep_mods2:
                # Dependency modified in both scenarios
                field_diffs = {}
                
                for field in ["dependency_type", "lag", "action"]:
                    if field in mod1 and field in mod2 and mod1[field] != mod2[field]:
                        field_diffs[field] = {
                            "scenario1": mod1[field],
                            "scenario2": mod2[field]
                        }
                
                if field_diffs:
                    dependency_diffs.append({
                        "from_task_id": mod1.get("from_task_id"),
                        "to_task_id": mod1.get("to_task_id"),
                        "in_both_scenarios": True,
                        "differences": field_diffs
                    })
            
            elif key in dep_mods1:
                # Dependency only in scenario1
                dependency_diffs.append({
                    "from_task_id": mod1.get("from_task_id"),
                    "to_task_id": mod1.get("to_task_id"),
                    "only_in_scenario1": True,
                    "modifications": mod1
                })
            
            else:
                # Dependency only in scenario2
                dependency_diffs.append({
                    "from_task_id": mod2.get("from_task_id"),
                    "to_task_id": mod2.get("to_task_id"),
                    "only_in_scenario2": True,
                    "modifications": mod2
                })
        
        return {
            "task_modifications": task_diffs,
            "resource_modifications": resource_diffs,
            "dependency_modifications": dependency_diffs
        }
